from sqlalchemy.orm import Session

from common.models import AnalysisBatch, AnalysisJob, Feedback, Workspace
from common.repositories.backfills import batch_view
from common.repositories.coordination import lock_workspace
from common.repositories.feedback import hydrate
from common.schemas.feedback import Snapshot


def snapshot(session: Session, workspace_id: str = "test") -> Snapshot:
    lock_workspace(session)

    cursor = (
        session.query(Workspace.cursor)
        .filter(Workspace.id == workspace_id)
        .with_for_update(read=True)
        .scalar()
    )
    record_ids = [
        row[0]
        for row in session.query(Feedback.id)
        .filter(Feedback.workspace_id == workspace_id)
        .order_by(Feedback.sequence.desc())
        .all()
    ]
    records = hydrate(session, workspace_id, record_ids)
    jobs = (
        session.query(AnalysisJob)
        .filter(AnalysisJob.workspace_id == workspace_id, AnalysisJob.origin != "analysis")
        .all()
    )
    batches = session.query(AnalysisBatch).filter(AnalysisBatch.workspace_id == workspace_id).all()

    return Snapshot(
        workspace_id=workspace_id,
        cursor=cursor or 0,
        records=records,
        batches=[batch_view(batch, jobs) for batch in batches],
    )
