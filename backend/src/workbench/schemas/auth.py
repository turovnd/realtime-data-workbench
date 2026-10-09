from typing import Literal

from pydantic import Field, field_validator

from workbench.schemas.common import StrictModel


class Credentials(StrictModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(
        min_length=12,
        max_length=128,
        description="12–128 character password; hashed with Argon2id",
        json_schema_extra={"writeOnly": True},
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class Identity(StrictModel):
    workspace_id: str
    email: str | None
    kind: Literal["account", "demo"]


class SessionResult(Identity):
    token: str = Field(
        description="Opaque bearer token, valid for 24 hours; stored hashed by the server"
    )
