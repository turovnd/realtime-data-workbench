import base64
import json
from uuid import uuid4

import pytest

from workbench.logic.activity_cursors import decode_activity_cursor
from workbench.logic.cursors import encode_cursor
from workbench.logic.errors import CursorError


def test_activity_positions_allow_larger_views_without_changing_feed_cursor_bounds() -> None:
    view_id = str(uuid4())
    for position in (0, 501, 502, 6000):
        assert decode_activity_cursor(encode_cursor(view_id, position, "secret"))[:2] == (
            view_id,
            position,
        )


@pytest.mark.parametrize(
    "value", [["bad-id", 1], [str(uuid4()), True], [str(uuid4()), -1], [str(uuid4()), 6001], {}, []]
)
def test_activity_cursor_rejects_invalid_shapes_and_positions(value: object) -> None:
    payload = base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")
    with pytest.raises(CursorError):
        decode_activity_cursor(payload + "." + "a" * 64)
