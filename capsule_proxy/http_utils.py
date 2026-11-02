import json

def send_bytes(handler, body, status=200, content_type="application/octet-stream",
               extra_headers=None, suppress_body=False):
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    if extra_headers:
        for name, value in extra_headers.items():
            handler.send_header(name, value)
    handler.send_header("Connection", "close")
    handler.end_headers()
    if not suppress_body and handler.command != "HEAD":
        handler.wfile.write(body)
    handler.close_connection = True


def send_json(handler, data, status=200):
    body = json.dumps(
        data, ensure_ascii=False, separators=(",", ":"), default=str
    ).encode("utf-8")
    send_bytes(
        handler, body, status,
        "application/json; charset=utf-8",
        suppress_body=handler.command == "HEAD",
    )
