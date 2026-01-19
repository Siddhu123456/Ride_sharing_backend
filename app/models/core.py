from typing import Optional

from sqlalchemy import Column, String, Text, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, AuditMixin


class Country(Base):
    __tablename__ = "country"

    country_code = Column(String(2), primary_key=True)
    name = Column(Text, nullable=False)

    default_timezone = Column(Text, nullable=False)
    default_currency = Column(String(3), nullable=False)

    phone_code = Column(String(6), nullable=False)


class City(Base):
    __tablename__ = "city"

    city_id = Column(BigInteger, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey("country.country_code"), nullable=False)

    name = Column(String, nullable=False)
    timezone = Column(String, nullable=False)
    currency = Column(String(3), nullable=False)

    __table_args__ = (
        UniqueConstraint("country_code", "name", name="uq_city_country_name"),
    )


class Zone(Base, AuditMixin):
    __tablename__ = "zone"
    zone_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    city_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("city.city_id"))
    name: Mapped[str] = mapped_column(String(120))
    boundary: Mapped[Optional[str]] = mapped_column(Text)