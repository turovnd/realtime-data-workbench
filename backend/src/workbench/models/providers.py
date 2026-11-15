from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from workbench.models.base import Base


class ProviderUsage(Base):
    __tablename__ = "provider_usage"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    calls: Mapped[int] = mapped_column(Integer, nullable=False)
