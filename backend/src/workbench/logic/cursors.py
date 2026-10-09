import base64
import hashlib
import hmac
import json
import re

from workbench.logic.errors import CursorError


def encode_cursor(view_id: str, before: int, secret: str) -> str:
    payload = (
        base64.urlsafe_b64encode(json.dumps([view_id, before], separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + signature


def decode_cursor(cursor: str) -> tuple[str, int, str, str]:
    try:
        if len(cursor) > 300:
            raise ValueError
        payload, signature = cursor.split(".")
        if not re.fullmatch(r"[a-f0-9]{64}", signature):
            raise ValueError
        decoded: object = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if (
            not isinstance(decoded, list)
            or len(decoded) != 2
            or not isinstance(decoded[0], str)
            or type(decoded[1]) is not int
        ):
            raise ValueError
        if not 0 <= decoded[1] <= 501:
            raise ValueError
        return decoded[0], decoded[1], payload, signature
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise CursorError("Invalid feedback cursor") from exc
