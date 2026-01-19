from datetime import datetime
from typing import Optional

from sqlalchemy import func, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_on: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_on: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())

class AuditMixin(TimestampMixin):
    @declared_attr
    def created_by(cls) -> Mapped[Optional[int]]:
        return mapped_column(BigInteger, nullable=True)

    @declared_attr
    def updated_by(cls) -> Mapped[Optional[int]]:
        return mapped_column(BigInteger, nullable=True)