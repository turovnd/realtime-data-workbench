from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from common.models import (
    Account,
    AnalysisBatch,
    AnalysisJob,
    AnalysisResult,
    AuthSession,
    Feedback,
    FeedView,
    Workspace,
)


def cleanup_expired(session: Session) -> int:
    now = datetime.now(UTC)
    session.query(FeedView).filter(FeedView.expires_at <= now).delete()
    session.query(AuthSession).filter(AuthSession.expires_at <= now).delete()
    expired = [
        row[0]
        for row in session.query(Workspace.id)
        .filter(
            Workspace.created_at < now - timedelta(hours=24),
            ~Workspace.id.in_(session.query(Account.workspace_id)),
        )
        .limit(20)
        .all()
    ]
    if not expired:
        return 0

    session.execute(text("SET LOCAL workbench.maintenance = 'on'"))

    for model in (AuthSession, FeedView, AnalysisResult, AnalysisJob, AnalysisBatch, Feedback):
        session.query(model).filter(model.workspace_id.in_(expired)).delete()

    session.query(Workspace).filter(Workspace.id.in_(expired)).delete()
    session.execute(text("SET LOCAL workbench.maintenance = 'off'"))

    return len(expired)
