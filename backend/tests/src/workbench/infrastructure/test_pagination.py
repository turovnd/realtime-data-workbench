import base64
import json
from uuid import uuid4

import pytest

from workbench.infrastructure.pagination import decode_cursor, encode_cursor, verify_cursor
from workbench.logic.errors import CursorError


@pytest.mark.parametrize("position", [0, 501, 502, 6000, 6001])
def test_round_trip_is_independent_of_each_list_capacity(position: int) -> None:
    view_id = str(uuid4())
    decoded = decode_cursor(encode_cursor(view_id, position, "view-secret"))
    assert decoded.view_id == view_id
    assert decoded.position == position
    verify_cursor(decoded, "view-secret")


def test_existing_cursor_format_remains_compatible() -> None:
    token = (
        "WyI2MTYyMjhhZi00MGM4LTRhNjUtOTVkZC1lNzY1ZTI4ZmRjMDMiLDEyXQ."
        "d393a8ece94871c41f84577aa075fad2f0f68121b82e8a716e16e3803e55fbbb"
    )
    decoded = decode_cursor(token)
    assert decoded.view_id == "616228af-40c8-4a65-95dd-e765e28fdc03"
    assert decoded.position == 12
    verify_cursor(decoded, "compatibility-secret")


@pytest.mark.parametrize(
    "value",
    [["bad-id", 1], [str(uuid4()), True], [str(uuid4()), -1], [str(uuid4()), 1.5], {}, []],
)
def test_invalid_payload_shape_is_rejected(value: object) -> None:
    payload = base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")
    with pytest.raises(CursorError):
        decode_cursor(payload + "." + "a" * 64)


@pytest.mark.parametrize("token", ["invalid", "a" * 301, "!." + "a" * 64, "A." + "a" * 64])
def test_malformed_envelope_is_rejected(token: str) -> None:
    with pytest.raises(CursorError):
        decode_cursor(token)


def test_signature_binds_view_position_and_signing_key() -> None:
    original = decode_cursor(encode_cursor(str(uuid4()), 10, "view-secret"))
    with pytest.raises(CursorError):
        verify_cursor(original, "another-secret")
    changed = encode_cursor(original.view_id, 11, "view-secret").split(".")[0]
    forged = decode_cursor(changed + "." + original.signature)
    with pytest.raises(CursorError):
        verify_cursor(forged, "view-secret")
