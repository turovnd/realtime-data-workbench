"""Feedback persistence within the caller's ingestion transaction."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from workbench.models import Feedback
from workbench.schemas.feedback import FeedbackInput


async def record_counts(session: AsyncSession, workspace_id: str) -> tuple[int, int]:
    own = await session.scalar(
        select(func.count()).select_from(Feedback).where(Feedback.workspace_id == workspace_id)
    )
    total = await session.scalar(select(func.count()).select_from(Feedback))
    return own or 0, total or 0


async def find_input(session: AsyncSession, workspace_id: str, identity: str) -> Feedback | None:
    return await session.scalar(
        select(Feedback).where(Feedback.workspace_id == workspace_id, Feedback.identity == identity)
    )


async def insert_input(
    session: AsyncSession, workspace_id: str, record_id: str, sequence: int, value: FeedbackInput
) -> None:
    session.add(
        Feedback(
            id=record_id,
            workspace_id=workspace_id,
            identity=value.identity,
            sequence=sequence,
            text=value.text,
            channel=value.channel,
            ingested_at=datetime.now(UTC),
        )
    )
    await session.flush()
