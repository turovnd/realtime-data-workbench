"""Persist admission for each paid attempt before contacting the provider."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from common.models import ProviderUsage
from common.repositories.coordination import lock_workspace


def reserve_live_call(session: Session, budget: int | None, provider: str = "openrouter") -> bool:
    """Count attempts across providers; switching never resets the lifetime ceiling.

    Existing OpenRouter reservations remain in their row. The serialized sum includes
    all provider rows, then increments only the provider admitting this attempt.
    """
    lock_workspace(session)
    used = int(session.query(func.sum(ProviderUsage.calls)).scalar() or 0)
    if budget is not None and used >= budget:
        return False
    usage = session.get(ProviderUsage, provider)
    if usage is None:
        session.add(ProviderUsage(id=provider, calls=1))
    else:
        usage.calls += 1
    return True
