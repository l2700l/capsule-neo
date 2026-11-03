"""Mock endpoint registry. Each route points to a function, not a response dict."""
import re
import uuid

from .handlers.device import get_firmware, set_stat
from .handlers.settings import (
    get_reminders, get_night_mode, set_night_mode,
    get_content_privacy, get_safe_mode, update_general, get_general,
    get_alarm_music, get_alarms,
)
from .handlers.logs import send_runtime_logs
from .handlers.websocket import send_websocket_ping

ROUTES = [
    ("GET", re.compile(r"^/device/firmware$"), None, get_firmware),
    ("POST", re.compile(r"^/device/stat$"), None, set_stat),
    ("GET", re.compile(r"^/account/settings/v1/reminders$"), None, get_reminders),
    ("POST", re.compile(r"^/rt_logs/send$"), "application/x-msgpack", send_runtime_logs),
    ("GET", re.compile(r"^/device/settings/v1/[^/]+/night_mode$"), None, get_night_mode),
    ("PUT", re.compile(r"^/device/settings/v1/[^/]+/night_mode/[^/]+$"), None, set_night_mode),
    ("GET", re.compile(r"^/device/settings/v1/[^/]+/content_privacy$"), None, get_content_privacy),
    ("GET", re.compile(r"^/device/settings/v1/[^/]+/safe_mode$"), None, get_safe_mode),
    ("PUT", re.compile(r"^/device/settings/v1/[^/]+/general/[^/]+$"), None, update_general),
    ("GET", re.compile(r"^/device/settings/v1/[^/]+/general$"), None, get_general),
    ("GET", re.compile(r"^/device/settings/v1/[^/]+/alarm_music$"), None, get_alarm_music),
    ("GET", re.compile(r"^/device/settings/v1/[^/]+/alarms$"), None, get_alarms),
    ("POST", re.compile(r"^/websocket/ping$"), None, send_websocket_ping),
]


def find_route(method, path, content_type):
    for route_method, pattern, expected_type, callback in ROUTES:
        if route_method != method or not pattern.fullmatch(path):
            continue
        if expected_type and expected_type not in content_type.lower():
            continue
        return {
            "method": route_method,
            "path": pattern.pattern,
            "callback": callback,
        }
    return None


def invoke_route(handler, route, body):
    result = route["callback"](handler, body)
    if isinstance(result, tuple) and len(result) == 3:
        status, response_obj, response_type = result
    else:
        status, response_obj, response_type = 200, result, "json"

    if isinstance(response_obj, dict):
        response_obj = response_obj.copy()
        response_obj["qid"] = uuid.uuid4().hex

    if response_type == "msgpack":
        import msgpack
        from .http_utils import send_bytes
        send_bytes(handler, msgpack.packb(response_obj, use_bin_type=True),
                   status, "application/x-msgpack",
                   suppress_body=handler.command == "HEAD")
    elif response_type == "raw":
        from .http_utils import send_bytes
        send_bytes(handler, response_obj, status, "application/octet-stream",
                   suppress_body=handler.command == "HEAD")
    else:
        from .http_utils import send_json
        send_json(handler, response_obj, status)
