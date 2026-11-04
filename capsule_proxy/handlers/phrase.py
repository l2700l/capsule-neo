import json
import uuid
from datetime import datetime, timezone
import http.client
from urllib.parse import urlsplit

from ..config import ASSISTANT_URL, CAPTURE_DIR
from ..logging_utils import safe_headers
from ..upstream import filtered_headers

def _capture_dir():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = CAPTURE_DIR / f"{timestamp}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path

def proxy_to_assistant(handler, body=None, transform_result=False):
    capture_dir = _capture_dir()
    request_id = capture_dir.name.rsplit("_", 1)[-1]

    target = urlsplit(ASSISTANT_URL)

    if not target.hostname:
        raise ValueError(f"Invalid ASSISTANT_URL: {ASSISTANT_URL}")

    connection_class = (
        http.client.HTTPSConnection
        if target.scheme == "https"
        else http.client.HTTPConnection
    )

    conn = connection_class(
        target.hostname,
        target.port,
        timeout=90,
    )

    base_path = target.path.rstrip("/")
    request_path = base_path + handler.path

    headers = handler.headers

    try:
        if body is not None:
            (capture_dir / "request_body.bin").write_bytes(body)

        (capture_dir / "request.json").write_text(
            json.dumps({
                "id": request_id,
                "time": datetime.now(timezone.utc).isoformat(),
                "client_ip": handler.client_address[0],
                "method": handler.command,
                "url": f"{ASSISTANT_URL}{handler.path}",
                "headers": safe_headers(handler.headers),
                "body_bytes": len(body) if body else 0,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        conn.request(
            handler.command,
            request_path,
            body=body,
            headers=headers,
        )

        upstream = conn.getresponse()
        response_body = upstream.read()
        response_headers = upstream.getheaders()

        content_type = next(
            (v for k, v in response_headers if k.lower() == "content-type"),
            "application/json",
        )

        # Сохраняем прежнюю подмену ссылок на радио
        if transform_result and "json" in content_type.lower():
            try:
                payload = json.loads(response_body)
                response_body = json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")

                (capture_dir / "response_modified.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        (capture_dir / "response_body.bin").write_bytes(response_body)

        (capture_dir / "response.json").write_text(
            json.dumps({
                "id": request_id,
                "status": upstream.status,
                "reason": upstream.reason,
                "headers": response_headers,
                "body_bytes": len(response_body),
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        handler.send_response(upstream.status, upstream.reason)

        handler.send_header("Content-Length", str(len(response_body)))
        handler.send_header("Connection", "close")
        handler.end_headers()

        if handler.command != "HEAD":
            handler.wfile.write(response_body)

        handler.close_connection = True

        print(
            f"[ASSISTANT PROXY] {handler.path} -> "
            f"{upstream.status}, capture={capture_dir}"
        )

    except Exception as exc:
        (capture_dir / "error.json").write_text(
            json.dumps({
                "id": request_id,
                "error": repr(exc),
            }, indent=2),
            encoding="utf-8",
        )

        print(f"[ASSISTANT PROXY ERROR] {handler.path}: {exc!r}")

        try:
            handler.send_error(502, "Assistant proxy error")
        except (BrokenPipeError, ConnectionError):
            pass

        handler.close_connection = True

    finally:
        conn.close()