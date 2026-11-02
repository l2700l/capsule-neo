import json
import msgpack


def parse_body(body, content_type):
    if not body:
        return {}
    try:
        lowered = content_type.lower()
        if "application/x-msgpack" in lowered:
            return msgpack.unpackb(body, raw=False, strict_map_key=False)
        if "application/json" in lowered:
            return json.loads(body.decode("utf-8"))
        return {"raw_hex": body[:256].hex(), "length": len(body)}
    except Exception as exc:
        return {
            "parse_error": str(exc),
            "raw_hex": body[:256].hex(),
            "length": len(body),
        }
