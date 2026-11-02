def get_firmware(handler, body=b""):
    # Sanitized mock values: never publish a real device identifier/QID.
    return 200, {
        "result": {
            "platform": "capsula-neo-1",
            "version": "3.5",
            "ts": 1739105548.0935233,
            "capabilities": "0",
            "filename": "3.5",
            "description": None,
            "need_auth": False,
            "source": "cdn",
            "label": "stable",
            "url": "https://vcfw.vkcdn.ru/capsula-neo-1/3.5?device_id=REDACTED&_qid=REDACTED&device_ver=3.5",
            "need_update": False,
        }
    }, "json"
