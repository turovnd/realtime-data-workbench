"""Signed continuation tokens; list membership and position bounds belong to callers."""

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field
from uuid import UUID

from common.logic.errors import CursorError

MAX_CURSOR_LENGTH = 300


@dataclass(frozen=True)
class Cursor:
    view_id: str
    position: int
    payload: str = field(repr=False)
    signature: str = field(repr=False)


def encode_cursor(view_id: str, position: int, secret: str) -> str:
    payload = (
        base64.urlsafe_b64encode(json.dumps([view_id, position], separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def decode_cursor(token: str) -> Cursor:
    """Parse an opaque token before loading its signing key from the stored view."""
    try:
        if len(token) > MAX_CURSOR_LENGTH:
            raise ValueError
        payload, signature = token.split(".")
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
        if type(position) is not int or position < 0:
            raise ValueError
        return Cursor(view_id, position, payload, signature)
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise CursorError("Invalid pagination cursor") from exc


def verify_cursor(cursor: Cursor, secret: str) -> None:
    """Verify exactly the payload that was signed, using a constant-time comparison."""
    expected = hmac.new(secret.encode(), cursor.payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(cursor.signature, expected):
        raise CursorError("Invalid pagination cursor")
