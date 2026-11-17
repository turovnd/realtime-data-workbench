from pydantic import Field, field_validator

from common.schemas.common import StrictModel


class AnalysisInput(StrictModel):
    identity: str = Field(
        min_length=1,
        max_length=100,
        description="Unique submission identity retained across retries",
    )

    @field_validator("identity")
    @classmethod
    def valid_identity(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("Identity must be nonblank and contain no null characters")
        return value
