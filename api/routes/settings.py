
import json

from fastapi import APIRouter, Request

from utils.responses import json_response
import asyncio

import math


ALARM_FIELDS = {
    "enabled",
    "alarm_time",
    "weekdays",
    "first_time",
}

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

async def refresh_alarms_after_delay(
    state,
    websocket_server,
    refreshes,
):
    await asyncio.sleep(60)

    state.complete_alarm_refresh(refreshes)

    try:
        await websocket_server.send_ping()
    except Exception:
        state.retry_alarm_refresh(refreshes)
        raise
@router.get("/device/settings/v1/{device_id}/alarms")
async def get_alarms(request: Request, device_id: str):
    state = request.app.state.device_state

    alarms, refreshes = state.sync_alarms()

    if refreshes:
        websocket_server = request.app.state.websocket_server

        tasks = getattr(
            request.app.state,
            "alarm_refresh_tasks",
            None,
        )

        if tasks is None:
            tasks = set()
            request.app.state.alarm_refresh_tasks = tasks

        task = asyncio.create_task(
            refresh_alarms_after_delay(
                state,
                websocket_server,
                refreshes,
            )
        )

        tasks.add(task)
        task.add_done_callback(tasks.discard)

    return json_response({
        "result": alarms,
    })

def validate_alarm_data(data: dict, creating: bool = False):
    unknown = set(data) - ALARM_FIELDS

    if unknown:
        return "invalid_fields"

    if creating and "alarm_time" not in data:
        return "missing_alarm_time"

    if "enabled" in data:
        if not isinstance(data["enabled"], bool):
            return "invalid_enabled"

    if "alarm_time" in data:
        value = data["alarm_time"]

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value < 86400
        ):
            return "invalid_alarm_time"

    if "weekdays" in data:
        weekdays = data["weekdays"]

        if (
            not isinstance(weekdays, list)
            or any(
                isinstance(day, bool)
                or not isinstance(day, int)
                or not 1 <= day <= 7
                for day in weekdays
            )
            or len(weekdays) != len(set(weekdays))
        ):
            return "invalid_weekdays"

    if "first_time" in data:
        value = data["first_time"]

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            return "invalid_first_time"

    return None


@router.post("/device/settings/v1/{device_id}/alarms")
async def add_alarm(request: Request, device_id: str):
    data = await parse_json_object(request)

    if data is None:
        return json_response(
            {"error": "invalid_json"},
            status_code=400,
        )

    error = validate_alarm_data(data, creating=True)

    if error:
        return json_response(
            {"error": error},
            status_code=400,
        )

    state = request.app.state.device_state
    state.add_alarm(data)

    return json_response({
        "result": state.get_collection("alarms"),
    })


@router.put("/device/settings/v1/{device_id}/alarms/{alarm_id}")
async def update_alarm(
    request: Request,
    device_id: str,
    alarm_id: str,
):
    data = await parse_json_object(request)

    if data is None:
        return json_response(
            {"error": "invalid_json"},
            status_code=400,
        )

    error = validate_alarm_data(data)

    if error:
        return json_response(
            {"error": error},
            status_code=400,
        )

    state = request.app.state.device_state
    updated = state.update_alarm(alarm_id, data)

    if updated is None:
        return json_response(
            {"error": "alarm_not_found"},
            status_code=404,
        )

    return json_response({
        "result": state.get_collection("alarms"),
    })


@router.delete("/device/settings/v1/{device_id}/alarms/{alarm_id}")
async def delete_alarm(
    request: Request,
    device_id: str,
    alarm_id: str,
):
    state = request.app.state.device_state
    updated = state.disable_alarm(alarm_id)

    if updated is None:
        return json_response(
            {"error": "alarm_not_found"},
            status_code=404,
        )

    return json_response({
        "result": state.get_collection("alarms"),
    })
@router.delete("/device/settings/v1/{device_id}/alarms")
async def delete_all_alarms(request: Request, device_id: str):
    state = request.app.state.device_state
    alarms = state.disable_all_alarms()

    return json_response({
        "result": alarms,
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
