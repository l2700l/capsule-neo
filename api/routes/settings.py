
import json

from fastapi import APIRouter, Request

from utils.responses import json_response


router = APIRouter()


async def parse_json_object(request: Request):
    """Читает JSON-объект из тела запроса."""
    try:
        data = json.loads(await request.body() or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    return data if isinstance(data, dict) else None


@router.put("/device/settings/v1/{device_id}/general/{setting_id}")
async def update_general(request: Request, device_id: str, setting_id: str):
    data = await parse_json_object(request)

    if data is None:
        return json_response(
            {"error": "invalid_json"},
            status_code=400,
        )

    state = request.app.state.device_state
    state.update_settings("general", data)

    return json_response({
        "result": {
            "success": True,
        }
    })


@router.put("/device/settings/v1/{device_id}/night_mode/{setting_id}")
async def set_night_mode(request: Request, device_id: str, setting_id: str):
    data = await parse_json_object(request)

    if data is None:
        return json_response(
            {"error": "invalid_json"},
            status_code=400,
        )

    if "enabled" in data and not isinstance(data["enabled"], bool):
        return json_response(
            {"error": "invalid_enabled"},
            status_code=400,
        )

    state = request.app.state.device_state
    updated = state.update_settings("night_mode", data)

    return json_response({
        "result": [updated],
    })


@router.get("/device/settings/v1/{device_id}/alarms")
async def get_alarms(request: Request, device_id: str):
    state = request.app.state.device_state

    return json_response({
        "result": state.get_collection("alarms"),
    })


@router.get("/account/settings/v1/reminders")
async def get_reminders(request: Request):
    state = request.app.state.device_state

    return json_response({
        "result": state.get_collection("reminders"),
    })


@router.get("/device/settings/v1/{device_id}/night_mode")
async def get_night_mode(request: Request, device_id: str):
    state = request.app.state.device_state

    return json_response({
        "result": [state.get_settings("night_mode")],
    })


@router.get("/device/settings/v1/{device_id}/content_privacy")
async def get_content_privacy(request: Request, device_id: str):
    state = request.app.state.device_state

    return json_response({
        "result": [state.get_settings("content_privacy")],
    })


@router.get("/device/settings/v1/{device_id}/safe_mode")
async def get_safe_mode(request: Request, device_id: str):
    state = request.app.state.device_state

    return json_response({
        "result": [state.get_settings("safe_mode")],
    })


@router.get("/device/settings/v1/{device_id}/general")
async def get_general(request: Request, device_id: str):
    state = request.app.state.device_state

    return json_response({
        "result": [state.get_settings("general")],
    })


@router.get("/device/settings/v1/{device_id}/alarm_music")
async def get_alarm_music(request: Request, device_id: str):
    return json_response({
        "result": [],
    })
