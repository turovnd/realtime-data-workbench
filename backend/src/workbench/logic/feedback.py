"""Workspace-scoped detail reads and idempotent user-authored feedback submission."""

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.errors import NotFoundError
from workbench.logic.ingestion import ingest
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.feedback import hydrate
from workbench.repositories.ingestion import find_input
from workbench.schemas.feedback import FeedbackInput, RecordView


async def get_feedback(engine: AsyncEngine, workspace_id: str, record_id: str) -> RecordView:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        rows = await hydrate(session, workspace_id, [record_id])
    if not rows:
        raise NotFoundError("Feedback was not found")
    return rows[0]


async def create_feedback(
    engine: AsyncEngine, workspace_id: str, value: FeedbackInput, provider: str
) -> tuple[RecordView, bool]:
    inserted = await ingest(engine, [value], workspace_id, provider)
    async with session_scope(engine) as session:
        await lock_workspace(session)
        raw = await find_input(session, workspace_id, value.identity)
        if raw is None:
            raise NotFoundError("Feedback was not found")
        rows = await hydrate(session, workspace_id, [raw.id])
    return rows[0], inserted > 0
