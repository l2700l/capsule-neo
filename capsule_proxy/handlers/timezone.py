from pathlib import Path
from zoneinfo import TZPATH
from importlib.resources import files

from ..config import TIMEZONE_NAME
from ..http_utils import send_bytes

def serve_timezone_info(handler):
    timezone_name = TIMEZONE_NAME
    tz_data = None
    for base in TZPATH:
        candidate = Path(base) / timezone_name
        if candidate.is_file():
            tz_data = candidate.read_bytes()
            break
    if tz_data is None:
        try:
            tz_data = files("tzdata").joinpath(
                "zoneinfo", *timezone_name.split("/")
            ).read_bytes()
        except (ImportError, ModuleNotFoundError, FileNotFoundError):
            pass
    if tz_data is None:
        handler.send_error(500, "Timezone database unavailable")
        return
    send_bytes(handler, tz_data, 200, "application/octet-stream",
               {"Cache-Control": "no-cache"},
               suppress_body=handler.command == "HEAD")
