"""HTTP dependencies wired by the application factory; no ambient workspace state."""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.repositories.sessions import identity
from workbench.schemas.auth import Identity
from workbench.settings import Settings


def get_database() -> AsyncEngine:
    raise RuntimeError("Database dependency was not configured by create_app")


def get_settings() -> Settings:
    raise RuntimeError("Settings dependency was not configured by create_app")


Database = Annotated[AsyncEngine, Depends(get_database)]
AppSettings = Annotated[Settings, Depends(get_settings)]
session_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="WorkspaceBearer",
    description=(
        "Use the opaque token returned by POST /api/auth/register, /login or /demo. "
        "Sessions expire after 24 hours; logout revokes the current token. All "
        "protected reads and writes use its workspace."
    ),
)


async def access_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(session_bearer)],
) -> str:
    return credentials.credentials if credentials else ""


Token = Annotated[str, Depends(access_token)]


async def authenticated(database: Database, token: Token) -> Identity:
    person = await identity(database, token)
    if person is None:
        raise HTTPException(
            status_code=401, detail="Sign in to continue. Your session is missing or expired."
        )
    return person


Person = Annotated[Identity, Depends(authenticated)]


async def current_workspace(person: Person) -> str:
    return person.workspace_id


Workspace = Annotated[str, Depends(current_workspace)]
