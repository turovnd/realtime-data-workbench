from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from common.logic.errors import ConflictError
from common.models import Account, Workspace
from common.repositories.coordination import lock_workspace
from common.repositories.sessions import issue_session
from common.schemas.auth import SessionResult


def create_account(session: Session, email: str, password_hash: str) -> SessionResult:
    lock_workspace(session)

    existing = session.query(Account.id).filter(Account.email == email).scalar()
    if existing is not None:
        raise ConflictError("Unable to register with those details. Try signing in.")

    count = session.query(func.count()).select_from(Workspace).scalar()
    if count is not None and count >= 1000:
        raise ConflictError("Account capacity reached")

    workspace = Workspace(id=str(uuid4()), cursor=0, created_at=datetime.now(UTC))
    session.add(workspace)
    session.flush()

    account = Account(
        id=str(uuid4()),
        workspace_id=workspace.id,
        email=email,
        password_hash=password_hash,
    )
    session.add(account)
    session.flush()

    token = issue_session(session, workspace.id, account.id)

    return SessionResult(
        workspace_id=workspace.id,
        email=account.email,
        kind="account",
        token=token,
    )


def find_account(session: Session, email: str) -> Account | None:
    return session.query(Account).filter(Account.email == email).one_or_none()


def account_session(session: Session, account: Account) -> SessionResult:
    lock_workspace(session)
    token = issue_session(session, account.workspace_id, account.id)

    return SessionResult(
        workspace_id=account.workspace_id,
        email=account.email,
        kind="account",
        token=token,
    )
