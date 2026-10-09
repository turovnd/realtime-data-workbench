import pytest
from pydantic import ValidationError

from workbench.schemas.feedback import FeedbackInput


@pytest.mark.parametrize("text", [" ", "", "x" * 4001])
def test_invalid_input(text: str) -> None:
    with pytest.raises(ValidationError):
        FeedbackInput(identity="test", text=text, channel="Support")
