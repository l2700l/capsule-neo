
from fastapi import APIRouter

from utils.responses import json_response

router = APIRouter()

@router.get("/device/firmware")
async def get_firmware():
    return json_response({
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
    })


@router.post("/device/stat")
async def set_stat():
    return json_response({
        "result": {
            "validation_errors": None,
        }
    })
