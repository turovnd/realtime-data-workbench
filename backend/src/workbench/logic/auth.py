import asyncio
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.logic.errors import AuthenticationError
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.accounts import account_session, create_account, find_account
from workbench.repositories.sessions import create_session, identity
from workbench.schemas.auth import Credentials, SessionResult

hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
hash_slots = asyncio.Semaphore(2)
dummy_hash = hasher.hash(secrets.token_urlsafe(32))


async def register(engine: AsyncEngine, credentials: Credentials) -> SessionResult:
    async with hash_slots:
        password_hash = await asyncio.to_thread(hasher.hash, credentials.password)
    return await create_account(engine, credentials.email, password_hash)


async def login(engine: AsyncEngine, credentials: Credentials) -> SessionResult:
    account = await find_account(engine, credentials.email)
    encoded = str(account["password_hash"]) if account else dummy_hash
    try:
        async with hash_slots:
            await asyncio.to_thread(hasher.verify, encoded, credentials.password)
    except VerificationError as exc:
        raise AuthenticationError("Email or password is incorrect") from exc
    if account is None:
        raise AuthenticationError("Email or password is incorrect")
    return await account_session(engine, account)


async def create_demo(engine: AsyncEngine) -> SessionResult:
    token = await create_session(engine)
    person = await identity(engine, token)
    assert person is not None
    # Initial demo jobs remain deterministic even when live tests are configured.
    await ingest(engine, synthetic_inputs("welcome-1", 12), person.workspace_id)
    await ingest(engine, synthetic_inputs("welcome-2", 12), person.workspace_id)
    return SessionResult(**person.model_dump(), token=token)
