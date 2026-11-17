"""Admit one explicit provider analysis without replacing any prior result."""

from sqlalchemy.orm import Session

from common.logic.errors import NotFoundError
from common.repositories.coordination import changed, lock_workspace
from common.repositories.feedback import hydrate
from common.repositories.jobs import enqueue, find_analysis_request
from common.schemas.analysis import AnalysisInput
from common.schemas.feedback import RecordView


def start_analysis(
    session: Session, workspace_id: str, record_id: str, request: AnalysisInput, provider: str
) -> tuple[RecordView, bool]:
    lock_workspace(session)
    records = hydrate(session, workspace_id, [record_id])
    if not records:
        raise NotFoundError("Feedback was not found")
    if find_analysis_request(session, record_id, request.identity):
        return records[0], False
    enqueue(
        session,
        record_id,
        "v2",
        "analysis",
        workspace_id=workspace_id,
        provider=provider,
        request_identity=request.identity,
    )
    changed(session, workspace_id)
    return (hydrate(session, workspace_id, [record_id]))[0], True
