"""Admit one explicit provider analysis without replacing any prior result."""

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.errors import NotFoundError
from workbench.repositories.coordination import changed, lock_workspace
from workbench.repositories.feedback import hydrate
from workbench.repositories.jobs import enqueue, find_analysis_request
from workbench.schemas.analysis import AnalysisInput
from workbench.schemas.feedback import RecordView


async def start_analysis(
    engine: AsyncEngine, workspace_id: str, record_id: str, request: AnalysisInput, provider: str
) -> tuple[RecordView, bool]:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        records = await hydrate(session, workspace_id, [record_id])
        if not records:
            raise NotFoundError("Feedback was not found")
        if await find_analysis_request(session, record_id, request.identity):
            return records[0], False
        await enqueue(
            session,
            record_id,
            "v2",
            "analysis",
            workspace_id=workspace_id,
            provider=provider,
            request_identity=request.identity,
        )
        await changed(session, workspace_id)
        return (await hydrate(session, workspace_id, [record_id]))[0], True
