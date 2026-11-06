
from fastapi import APIRouter, Request, HTTPException

from utils.responses import msgpack_response


router = APIRouter()


@router.post("/rt_logs/send")
async def send_runtime_logs(request: Request):
    content_type = request.headers.get("content-type", "").lower()

    if "application/x-msgpack" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="Unsupported content type",
        )

    return msgpack_response({
        "result": {
            "success": True,
        }
    })
