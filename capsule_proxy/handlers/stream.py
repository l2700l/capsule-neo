import json
import uuid
from datetime import datetime, timezone

from ..config import UPSTREAM_HOST, UPSTREAM_IP, STREAM_CAPTURE_DIR
from ..logging_utils import safe_headers
from ..upstream import DirectHTTPSConnection, filtered_headers
from ..audio_streams import find_stream, serve_stream, stream_id_from_request


STREAM_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host",
}


def proxy_stream(handler):
    stream_id = stream_id_from_request(handler.path)
    local_stream = find_stream(stream_id)

    if local_stream is not None:
        serve_stream(handler, local_stream)
        print(f"[stream] Local audio: {stream_id}")
        return
    capture_dir = STREAM_CAPTURE_DIR / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        + "_" + uuid.uuid4().hex[:8]
    )
    capture_dir.mkdir(parents=True, exist_ok=True)
    request_headers = filtered_headers(handler.headers, STREAM_HOP_BY_HOP | {"content-length"})
    (capture_dir / "request.json").write_text(json.dumps({
        "time": datetime.now(timezone.utc).isoformat(),
        "method": handler.command, "path": handler.path,
        "headers": safe_headers(handler.headers),
        "upstream": f"https://{UPSTREAM_HOST}{handler.path}",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    conn = DirectHTTPSConnection(UPSTREAM_HOST, UPSTREAM_IP, timeout=60)
    record = {"started_at": datetime.now(timezone.utc).isoformat(),
              "status": None, "headers": [], "body_bytes": 0, "completed": False}
    received = 0
    headers_sent = False
    try:
        conn.request("GET", handler.path, headers=request_headers)
        upstream = conn.getresponse()
        record["status"] = upstream.status
        record["reason"] = upstream.reason
        record["headers"] = upstream.getheaders()
        handler.send_response(upstream.status, upstream.reason)
        for name, value in upstream.getheaders():
            if name.lower() not in STREAM_HOP_BY_HOP:
                handler.send_header(name, value)
        handler.send_header("Connection", "close")
        handler.end_headers()
        headers_sent = True
        with (capture_dir / "response_body.bin").open("wb") as body_file:
            while True:
                chunk = upstream.read1(8192)
                if not chunk:
                    break
                body_file.write(chunk)
                body_file.flush()
                handler.wfile.write(chunk)
                handler.wfile.flush()
                received += len(chunk)
        record["completed"] = True
    except Exception as exc:
        record["error"] = repr(exc)
        print(f"[stream] Proxy error: {exc!r}")
        if not headers_sent:
            try:
                handler.send_error(502, "Stream proxy error")
            except (BrokenPipeError, ConnectionError):
                pass
    finally:
        record["body_bytes"] = received
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        (capture_dir / "response.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        conn.close()
        handler.close_connection = True
        print(f"[stream] {handler.path} -> {record['status']}, {received} bytes captured in {capture_dir}")
