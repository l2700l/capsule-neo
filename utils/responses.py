
import uuid
from msgpack import msgpack
from fastapi.responses import JSONResponse, Response


def json_response(data: dict, status_code: int = 200):
    response_data = data.copy()
    response_data["qid"] = uuid.uuid4().hex

    return JSONResponse(
        content=response_data,
        status_code=status_code,
    )

def msgpack_response(data: dict, status_code: int = 200):
    response_data = data.copy()
    response_data["qid"] = uuid.uuid4().hex

    return Response(
        content=msgpack.packb(
            response_data,
            use_bin_type=True,
        ),
        status_code=status_code,
        media_type="application/x-msgpack",
    )
