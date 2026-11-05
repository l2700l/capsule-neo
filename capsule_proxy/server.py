from pathlib import Path
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from .config import CAPTURE_DIR, HOST, PORT, MAX_BODY, KNOWN_LOG, UNKNOWN_LOG, UPSTREAM_HOST
from .http_utils import send_json
from .logging_utils import append_jsonl, safe_headers, make_curl
from .parsing import parse_body
from .routes import find_route, invoke_route
from .handlers.phrase import proxy_to_assistant
from .handlers.stream import proxy_stream
# from .handlers.phrase_proxy import proxy_phrase_create, proxy_phrase_result
from .handlers.radio import serve_test_radio
from .handlers.timezone import serve_timezone_info
from . import websocket
from .state import DeviceState
from .config import TIMEZONE_NAME
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def read_request_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length < 0:
            length = 0
        return self.rfile.read(length) if length else b""

    def handle_request(self):
        parsed = urlsplit(self.path)
        path, query = parsed.path, parsed.query
        if path == "/device/timezone/info":
            serve_timezone_info(self)
            return
        if self.command == "GET" and path == "/phrase/result":
            proxy_to_assistant(self, transform_result=True)
            return
        # if self.command == "GET" and path == "/phrase/result":
        #     proxy_phrase_result(self)
        #     return
        if self.command == "GET" and path == "/radio.mp3":
            serve_test_radio(self)
            return

        body = self.read_request_body()

        if self.command == "GET" and path == "/stream":
            proxy_stream(self)
            return
        # TODO: добавить stt и классификатор, сейчас запросы проксируются на сервера ВК
        # if self.command == "POST" and (
        #     path.startswith("/phrase/create") or path.startswith("/phrase/add")
        # ):
        #     proxy_phrase_create(self, body)
        #     return
        # if self.command == "GET" and path == "/stream":
        #     proxy_stream(self)
        #     return
        # # TODO: добавить stt и классификатор, сейчас запросы проксируются на сервера ВК
        if self.command == "POST" and (
            path.startswith("/phrase/create") or path.startswith("/phrase/add")
        ):
            proxy_to_assistant(self, body)
            return
        body_file = None

        if body:
            body_dir = CAPTURE_DIR / "request_bodies"
            body_dir.mkdir(parents=True, exist_ok=True)

            body_file = body_dir / f"{uuid.uuid4().hex}.bin"
            body_file.write_bytes(body)
        logged_body = body[:MAX_BODY]
        content_type = self.headers.get("Content-Type", "")
        parsed_body = parse_body(logged_body, content_type)
        url = f"https://{UPSTREAM_HOST}{self.path}"
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "client_ip": self.client_address[0],
            "method": self.command,
            "path": path,
            "query": query,
            "headers": safe_headers(self.headers),
            "body_bytes_received": len(body),
            "body_bytes_logged": len(logged_body),
            "body_truncated": len(body) > MAX_BODY,
            "body": parsed_body,
            "curl": make_curl(self.command, url, dict(self.headers.items()), body_file=body_file),
            "body_file": str(body_file) if body_file else None
        }

        route = find_route(self.command, path, content_type)
        if route:
            record.update({
                "known": True,
                "route": route["path"],
                "response_status": 200,
                "handler": route["callback"].__name__,
            })
            append_jsonl(KNOWN_LOG, record)
            invoke_route(self, route, body)
            return

        record.update({
            "known": False,
            "reason": "No matching method/path/content-type route",
        })
        for key, value in record.items():
            if isinstance(value, bytes):
                print(f"[DEBUG] record[{key!r}] contains bytes: {len(value)} bytes")
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, bytes):
                        print(
                            f"[DEBUG] record[{key!r}][{subkey!r}] "
                            f"contains bytes: {len(subvalue)} bytes"
                        )

        append_jsonl(UNKNOWN_LOG, record)
        send_json(self, {
            "ok": False,
            "error": "unknown_endpoint",
            "method": self.command,
            "path": path,
        }, status=404)

    do_GET = handle_request
    do_POST = handle_request
    do_PUT = handle_request
    do_PATCH = handle_request
    do_DELETE = handle_request
    do_OPTIONS = handle_request
    do_HEAD = handle_request


def main():
    websocket.start_background()

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.device_state = DeviceState(TIMEZONE_NAME, storage_path=Path("device_state.json"))

    print(f"Listening on http://{HOST}:{PORT}")
    print(f"Known requests:   {KNOWN_LOG}")
    print(f"Unknown requests: {UNKNOWN_LOG}")
    print(f"Sensitive header redaction: {'ON' if __import__('capsule_proxy.config', fromlist=['REDACT_SENSITIVE_HEADERS']).REDACT_SENSITIVE_HEADERS else 'OFF'}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        try:
            server.device_state.save()
            print("[STATE] Saved successfully")
        except OSError as exc:
            print(f"[STATE] Failed to save: {exc}")
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
