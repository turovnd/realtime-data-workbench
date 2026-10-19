import base64
import json
import re
from uuid import UUID

from workbench.logic.errors import CursorError


def decode_activity_cursor(cursor: str) -> tuple[str, int, str, str]:
    try:
        if len(cursor) > 300:
            raise ValueError
        payload, signature = cursor.split(".")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", payload):
            raise ValueError
        if not re.fullmatch(r"[a-f0-9]{64}", signature):
            raise ValueError
        decoded: object = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if not isinstance(decoded, list) or len(decoded) != 2:
            raise ValueError
        view_id, position = decoded
        if not isinstance(view_id, str) or str(UUID(view_id)) != view_id:
            raise ValueError
        if type(position) is not int or not 0 <= position <= 6000:
            raise ValueError
        return view_id, position, payload, signature
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise CursorError("Invalid activity cursor") from exc
