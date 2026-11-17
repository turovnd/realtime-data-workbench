"""Serialize bounded demo operations and advance affected workspace revisions."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from common.models import Workspace


def lock_workspace(session: Session) -> None:
    # This is intentionally a process-independent global admission lock: capacity
    # and provider budgets are shared across workspaces in this bounded demo.
    session.execute(text("SELECT pg_advisory_xact_lock(72100692)"))


def changed(session: Session, workspace_id: str = "test") -> None:
    session.query(Workspace).filter(Workspace.id == workspace_id).update(
        {Workspace.cursor: Workspace.cursor + 1}
    )
