import json


def _parse_json_object(body):
    if isinstance(body, str):
        body = body.encode("utf-8")

    try:
        data = json.loads(body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    return data if isinstance(data, dict) else None


def update_general(handler, body=b""):
    data = _parse_json_object(body)

    if data is None:
        return 400, {"error": "invalid_json"}, "json"

    state = handler.server.device_state

    # Обновляются только известные поля настроек.
    updated = state.update_settings("general", data)

    return {"result": {"success": True}}


def set_night_mode(handler, body=b""):
    data = _parse_json_object(body)

    if data is None:
        return 400, {"error": "invalid_json"}, "json"

    if "enabled" in data and not isinstance(data["enabled"], bool):
        return 400, {"error": "invalid_enabled"}, "json"

    state = handler.server.device_state
    updated = state.update_settings("night_mode", data)

    return {"result": [updated]}

def get_alarms(handler, body=b""):
    return {
        "result": handler.server.device_state.get_collection("alarms")
    }


def get_reminders(handler, body=b""):
    return {
        "result": handler.server.device_state.get_collection("reminders")
    }

def get_night_mode(handler, body=b""):
    state = handler.server.device_state
    return {"result": [state.get_settings("night_mode")]}


def get_content_privacy(handler, body=b""):
    state = handler.server.device_state
    return {"result": [state.get_settings("content_privacy")]}


def get_safe_mode(handler, body=b""):
    state = handler.server.device_state
    return {"result": [state.get_settings("safe_mode")]}

def get_general(handler, body=b""):
    state = handler.server.device_state
    return {"result": [state.get_settings("general")]}


def get_alarm_music(handler, body=b""):
    # не нашел способа получить что-то помимо пустого массива
    return {"result": []}
