
from pathlib import Path
from zoneinfo import TZPATH
from importlib.resources import files

from fastapi import APIRouter, Response, Request

from config import TIMEZONE_NAME


router = APIRouter()


def get_timezone_data():
    """Загружает бинарные данные часового пояса TZif."""
    for base in TZPATH:
        candidate = Path(base) / TIMEZONE_NAME

        if candidate.is_file():
            return candidate.read_bytes()

    try:
        return files("tzdata").joinpath(
            "zoneinfo",
            *TIMEZONE_NAME.split("/"),
        ).read_bytes()

    except (
        ImportError,
        ModuleNotFoundError,
        FileNotFoundError,
    ):
        return None


@router.api_route(
    "/device/timezone/info",
    methods=["GET", "HEAD"],
)
async def timezone_info(request: Request):
    tz_data = get_timezone_data()

    if tz_data is None:
        return Response(
            content="Timezone database unavailable",
            status_code=500,
        )

    return Response(
        content=b"" if request and request.method == "HEAD" else tz_data,
        status_code=200,
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-cache",
        },
    )
