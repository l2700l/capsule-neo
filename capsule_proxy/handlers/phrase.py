import json
import re
import uuid
from datetime import datetime, timezone

from ..config import UPSTREAM_HOST, UPSTREAM_IP, CAPTURE_DIR, LOCAL_RADIO_URL, RADIO_URL_PATTERN
from ..logging_utils import safe_headers
from ..upstream import DirectHTTPSConnection, filtered_headers
from ..http_utils import send_bytes
from ..protocol import Response

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade", "proxy-connection",
    "content-length", "host", "expect",
}
RADIO_URL_RE = re.compile(RADIO_URL_PATTERN)

def replace_radio_urls(value):
    if isinstance(value, dict):
        return {key: replace_radio_urls(item) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_radio_urls(item) for item in value]
    if isinstance(value, str):
        return RADIO_URL_RE.sub(LOCAL_RADIO_URL, value)
    return value


def _capture_dir():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = CAPTURE_DIR / f"{timestamp}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def proxy_phrase_create(handler, body):
    capture_dir = _capture_dir()
    request_id = capture_dir.name.rsplit("_", 1)[-1]
    (capture_dir / "request_body.bin").write_bytes(body)
    (capture_dir / "request.json").write_text(json.dumps({
        "id": request_id,
        "time": datetime.now(timezone.utc).isoformat(),
        "client_ip": handler.client_address[0],
        "method": handler.command,
        "url": f"https://{UPSTREAM_HOST}{handler.path}",
        "headers": safe_headers(handler.headers),
        "body_bytes": len(body),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    headers = filtered_headers(handler.headers, HOP_BY_HOP)
    conn = DirectHTTPSConnection(UPSTREAM_HOST, UPSTREAM_IP, timeout=90)
    try:
        conn.request(handler.command, handler.path, body=body, headers=headers)
        upstream = conn.getresponse()
        response_body = upstream.read()
        response_headers = upstream.getheaders()
        (capture_dir / "response_body.bin").write_bytes(response_body)
        content_type = next((v for k, v in response_headers if k.lower() == "content-type"), "")
        text_body = None
        if any(kind in content_type.lower() for kind in ("text/", "json", "xml")):
            text_body = response_body.decode("utf-8", errors="replace")
        (capture_dir / "response.json").write_text(json.dumps({
            "id": request_id, "status": upstream.status, "reason": upstream.reason,
            "headers": response_headers, "body_bytes": len(response_body),
            "body_text": text_body,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        handler.send_response(upstream.status, upstream.reason)
        for name, value in response_headers:
            if name.lower() in HOP_BY_HOP:
                continue
            handler.send_header(name, value)
        handler.send_header("Content-Length", str(len(response_body)))
        handler.send_header("Connection", "close")
        handler.end_headers()
        if handler.command != "HEAD":
            handler.wfile.write(response_body)
        handler.close_connection = True
        print(f"[PHRASE PROXY] {handler.path} -> {upstream.status}, capture={capture_dir}")
    except Exception as exc:
        (capture_dir / "error.json").write_text(json.dumps({"id": request_id, "error": repr(exc)}, indent=2), encoding="utf-8")
        print(f"[PHRASE PROXY ERROR] {handler.path}: {exc!r}")
        try:
            handler.send_error(502, "Upstream proxy error")
        except (BrokenPipeError, ConnectionError):
            pass
        handler.close_connection = True
    finally:
        conn.close()

def build_custom_phrase_result(intent):
    if intent == "music.play_track":
        response = Response(skill="custom", intent="custom.custom").say("Включаю анимацию дисплея").show_digits("CEF5", duration=4.0).delay(4000).bluetooth(True).delay(2000).bluetooth(False).delay(2000).to_dict()
        print(response)
        return response

    return None

def proxy_phrase_result(handler):
    capture_dir = _capture_dir()
    request_id = capture_dir.name.rsplit("_", 1)[-1]
    headers = filtered_headers(handler.headers, HOP_BY_HOP)
    conn = DirectHTTPSConnection(UPSTREAM_HOST, UPSTREAM_IP, timeout=90)
    try:
        conn.request("GET", handler.path, headers=headers)
        upstream = conn.getresponse()
        original_body = upstream.read()
        (capture_dir / "response_original.bin").write_bytes(original_body)
        content_type = next((v for k, v in upstream.getheaders() if k.lower() == "content-type"), "application/json")
        payload = json.loads(original_body)

        intent = (
            payload.get("result", {}).get("intent")
            if isinstance(payload, dict)
            else None
        )

        custom_payload = build_custom_phrase_result(intent)

        if custom_payload is not None:
            modified = custom_payload
            print(f"[PHRASE RESULT] Custom response for intent={intent}")
        else:
            modified = replace_radio_urls(payload)
        response_body = json.dumps(modified, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        (capture_dir / "response_modified.json").write_text(json.dumps(modified, ensure_ascii=False, indent=2), encoding="utf-8")
        (capture_dir / "response_body.bin").write_bytes(response_body)
        handler.send_response(upstream.status, upstream.reason)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(response_body)))
        handler.send_header("Connection", "close")
        handler.end_headers()
        if handler.command != "HEAD":
            handler.wfile.write(response_body)
        handler.close_connection = True
        print(f"[PHRASE RESULT] {handler.path} -> {upstream.status}, capture={capture_dir}")
    except Exception as exc:
        print(f"[PHRASE RESULT ERROR] {handler.path}: {exc!r}")
        try:
            handler.send_error(502, "phrase/result proxy error")
        except (BrokenPipeError, ConnectionError):
            pass
        handler.close_connection = True
    finally:
        conn.close()
