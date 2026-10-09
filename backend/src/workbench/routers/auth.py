from fastapi import APIRouter, Request

from workbench.dependencies import Database, Person, Token
from workbench.logic.auth import create_demo, login, register
from workbench.repositories.rate_limits import limit_auth
from workbench.repositories.sessions import logout
from workbench.routers.responses import errors
from workbench.schemas.auth import Credentials, Identity, SessionResult
from workbench.schemas.common import EmptyRequest, OkResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


async def admission(request: Request, database: Database, email: str | None = None) -> None:
    host = request.client.host if request.client else "unknown"
    await limit_auth(database, f"ip:{host}")
    if email:
        await limit_auth(database, f"email:{email}", 10)


@router.post(
    "/demo",
    response_model=SessionResult,
    operation_id="createDemoSession",
    summary="Open an isolated synthetic demo",
    description=(
        "Creates a temporary workspace and a revocable 24-hour bearer token. Seeds "
        "24 synthetic records with deterministic jobs, even when live provider "
        "tests are configured. Limited to 20 auth requests per IP per 15 minutes. "
        "Send an empty JSON object."
    ),
    responses=errors(403, 409, 413, 429),
)
async def demo(
    request: Request, database: Database, _body: EmptyRequest | None = None
) -> SessionResult:
    await admission(request, database)
    return await create_demo(database)


@router.post(
    "/register",
    response_model=SessionResult,
    operation_id="registerAccount",
    summary="Create an independent personal account",
    description=(
        "Creates an empty personal workspace. Passwords are hashed with Argon2id; "
        "they are never returned. Email is normalized to lowercase. No email "
        "verification or password reset is implemented. Limited by both IP and "
        "email."
    ),
    responses=errors(403, 409, 413, 429),
)
async def sign_up(credentials: Credentials, request: Request, database: Database) -> SessionResult:
    await admission(request, database, credentials.email)
    return await register(database, credentials)


@router.post(
    "/login",
    response_model=SessionResult,
    operation_id="loginAccount",
    summary="Sign in to an existing account",
    description=(
        "Returns a new opaque token for the existing workspace without deleting its "
        "records. Tokens expire after 24 hours; at most ten active sessions per "
        "account. Invalid credentials use a generic error. Email admission allows "
        "ten attempts per 15 minutes; IP admission allows twenty."
    ),
    responses=errors(401, 403, 409, 413, 429),
)
async def sign_in(credentials: Credentials, request: Request, database: Database) -> SessionResult:
    await admission(request, database, credentials.email)
    return await login(database, credentials)


@router.get(
    "/me",
    response_model=Identity,
    operation_id="getCurrentIdentity",
    summary="Read the current session identity",
    description=(
        "Validates the bearer token and returns only its workspace and account/demo identity."
    ),
    responses=errors(401),
)
async def me(person: Person) -> Identity:
    return person


@router.post(
    "/logout",
    response_model=OkResponse,
    operation_id="logoutSession",
    summary="Revoke the current bearer token",
    description=(
        "Revokes this token immediately. Other account sessions remain valid. The "
        "UI separately clears its private query and offline caches. Send an empty "
        "JSON object."
    ),
    responses=errors(401, 403, 413),
)
async def sign_out(
    database: Database, token: Token, _person: Person, _body: EmptyRequest | None = None
) -> OkResponse:
    await logout(database, token)
    return OkResponse()
