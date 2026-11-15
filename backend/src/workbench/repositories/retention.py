from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from workbench.models import (
    Account,
    AnalysisBatch,
    AnalysisJob,
    AnalysisResult,
    AuthSession,
    Feedback,
    FeedView,
    Workspace,
)


async def cleanup_expired(session: AsyncSession) -> int:
    now = datetime.now(UTC)
    await session.execute(delete(FeedView).where(FeedView.expires_at <= now))
    await session.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
    expired = list(
        await session.scalars(
            select(Workspace.id)
            .where(
                Workspace.created_at < now - timedelta(hours=24),
                ~Workspace.id.in_(select(Account.workspace_id)),
            )
            .limit(20)
        )
    )
    if not expired:
        return 0

    await session.execute(text("SET LOCAL workbench.maintenance = 'on'"))

    for model in (AuthSession, FeedView, AnalysisResult, AnalysisJob, AnalysisBatch, Feedback):
        await session.execute(delete(model).where(model.workspace_id.in_(expired)))

    await session.execute(delete(Workspace).where(Workspace.id.in_(expired)))
    await session.execute(text("SET LOCAL workbench.maintenance = 'off'"))

    return len(expired)
