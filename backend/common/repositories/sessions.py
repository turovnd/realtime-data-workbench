import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from common.logic.errors import ConflictError
from common.models import Account, AuthSession, Workspace
from common.repositories.coordination import lock_workspace
from common.repositories.retention import cleanup_expired
from common.repositories.security import digest
from common.schemas.auth import Identity


def issue_session(session: Session, workspace_id: str, account_id: str | None) -> str:
    now = datetime.now(UTC)
    session.query(AuthSession).filter(AuthSession.expires_at <= now).delete()
    count = (
        session.query(func.count())
        .select_from(AuthSession)
        .filter(AuthSession.workspace_id == workspace_id)
        .scalar()
    )
    if count is not None and count >= 10:
        raise ConflictError(
            "This account has ten active sessions. Sign out of an existing session first."
        )

    token = secrets.token_urlsafe(32)
    session.add(
        AuthSession(
            token_hash=digest(token),
            workspace_id=workspace_id,
            account_id=account_id,
            expires_at=now + timedelta(hours=24),
        )
    )
    session.flush()

    return token


def create_session(session: Session) -> str:
    """Create an independent temporary demo, never an implicit account login."""
    lock_workspace(session)
    cleanup_expired(session)

    count = session.query(func.count()).select_from(Workspace).scalar()
    if count is not None and count >= 1000:
        raise ConflictError("Demo capacity reached. Try again after temporary workspaces expire.")

    workspace = Workspace(id=str(uuid4()), cursor=0, created_at=datetime.now(UTC))
    session.add(workspace)
    session.flush()

    return issue_session(session, workspace.id, None)


def identity(session: Session, token: str) -> Identity | None:
    if not 32 <= len(token) <= 64:
        return None

    auth_session = (
        session.query(AuthSession)
        .filter(AuthSession.token_hash == digest(token), AuthSession.expires_at > datetime.now(UTC))
        .one_or_none()
    )
    if auth_session is None:
        return None

    account = (
        session.get(Account, auth_session.account_id)
        if auth_session.account_id is not None
        else None
    )

    return Identity(
        workspace_id=auth_session.workspace_id,
        email=account.email if account is not None else None,
        kind="account" if auth_session.account_id is not None else "demo",
    )


def resolve_session(session: Session, token: str) -> str | None:
    result = identity(session, token)

    return result.workspace_id if result is not None else None


def logout(session: Session, token: str) -> None:
    session.query(AuthSession).filter(AuthSession.token_hash == digest(token)).delete()
