def send_runtime_logs(handler, body=b""):
    return 200, {"result": {"success": True}}, "msgpack"
