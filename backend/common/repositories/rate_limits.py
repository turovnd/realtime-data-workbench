from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from common.logic.errors import RateLimitError
from common.models import AuthBucket
from common.repositories.coordination import lock_workspace
from common.repositories.security import digest


def limit_auth(session: Session, key: str, limit: int = 20) -> None:
    lock_workspace(session)

    now = datetime.now(UTC)
    session.query(AuthBucket).filter(AuthBucket.expires_at <= now).delete()
    name = digest(key)
    bucket = session.get(AuthBucket, name)

    if bucket is not None:
        if bucket.attempts >= limit:
            raise RateLimitError("Too many authentication attempts. Try again in 15 minutes.")

        bucket.attempts += 1
        return

    count = session.query(func.count()).select_from(AuthBucket).scalar()
    if count is not None and count >= 2000:
        raise RateLimitError("Authentication is temporarily busy. Try again later.")

    session.add(AuthBucket(key=name, attempts=1, expires_at=now + timedelta(minutes=15)))
