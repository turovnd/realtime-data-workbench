"""Read feedback with a bounded recent history for each record."""

from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from common.models import AnalysisJob, AnalysisResult, Feedback
from common.schemas.enrichment import OutputView
from common.schemas.feedback import JobView, RecordView


def job_view(job: AnalysisJob) -> JobView:
    return JobView.model_validate(job, from_attributes=True)


def output_view(output: AnalysisResult) -> OutputView:
    return OutputView.model_validate(
        {
            **output.payload,
            "config": output.config,
            "run": output.run,
            "provider": output.provider,
            "created_at": output.created_at.isoformat(),
        }
    )


def _recent_history[History: (AnalysisJob, AnalysisResult)](
    session: Session, model: type[History], workspace_id: str, ids: list[str]
) -> list[History]:
    ranked = (
        session.query(
            model.id,
            func.row_number()
            .over(partition_by=model.record_id, order_by=model.run.desc())
            .label("position"),
        )
        .filter(model.workspace_id == workspace_id, model.record_id.in_(ids))
        .subquery()
    )
    query: Query[History] = (
        session.query(model)
        .join(ranked, model.id == ranked.c.id)
        .filter(ranked.c.position <= 10)
        .order_by(model.run)
    )
    return query.all()


def hydrate(session: Session, workspace_id: str, ids: list[str]) -> list[RecordView]:
    records = (
        session.query(Feedback)
        .filter(Feedback.workspace_id == workspace_id, Feedback.id.in_(ids))
        .order_by(Feedback.sequence.desc())
        .all()
    )
    jobs = _recent_history(session, AnalysisJob, workspace_id, ids)
    outputs = _recent_history(session, AnalysisResult, workspace_id, ids)

    jobs_by_record: dict[str, list[JobView]] = defaultdict(list)
    for job in jobs:
        jobs_by_record[job.record_id].append(job_view(job))

    outputs_by_record: dict[str, list[OutputView]] = defaultdict(list)
    for output in outputs:
        outputs_by_record[output.record_id].append(output_view(output))

    return [
        RecordView(
            id=record.id,
            sequence=record.sequence,
            text=record.text,
            channel=record.channel,
            ingested_at=record.ingested_at.isoformat(),
            jobs=jobs_by_record[record.id],
            outputs=outputs_by_record[record.id],
        )
        for record in records
    ]
