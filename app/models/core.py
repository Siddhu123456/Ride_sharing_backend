from sqlalchemy import (
    Column,
    BigInteger,
    VARCHAR,
    CHAR,
    ForeignKey,
    TIMESTAMP,
    func,
    DECIMAL,
    UniqueConstraint,
    TEXT,
)
from geoalchemy2 import Geometry

from app.models.base import Base


class Country(Base):
    __tablename__ = "country"

    country_code = Column(CHAR(2), primary_key=True)
    name = Column(VARCHAR(100), nullable=False)
    phone_code = Column(VARCHAR(5), nullable=False)
    default_timezone = Column(VARCHAR(50), nullable=False)
    default_currency = Column(CHAR(3), nullable=False)

    created_by = Column(VARCHAR(20), nullable=False, server_default="admin")
    created_on = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_by = Column(BigInteger, nullable=True)
    updated_on = Column(TIMESTAMP(timezone=True), nullable=True)


class City(Base):
    __tablename__ = "city"
    __table_args__ = (
        UniqueConstraint("country_code", "name", name="uq_city_country_name"),
    )

    city_id = Column(BigInteger, primary_key=True, autoincrement=True)
    country_code = Column(CHAR(2), ForeignKey("country.country_code"), nullable=False)

    name = Column(VARCHAR(120), nullable=False)
    timezone = Column(VARCHAR(50), nullable=False)
    currency = Column(CHAR(3), nullable=False)

    # ✅ NEW: city boundary polygon
    boundary = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)

    created_by = Column(VARCHAR(20), nullable=False, server_default="admin")
    created_on = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_by = Column(BigInteger, nullable=True)
    updated_on = Column(TIMESTAMP(timezone=True), nullable=True)


class Zone(Base):
    __tablename__ = "zone"
    __table_args__ = (
        UniqueConstraint("city_id", "name", name="uq_zone_city_name"),
    )

    zone_id = Column(BigInteger, primary_key=True, autoincrement=True)
    city_id = Column(BigInteger, ForeignKey("city.city_id"), nullable=False)

    name = Column(VARCHAR(120), nullable=False)

    center_lat = Column(DECIMAL(9, 6), nullable=True)
    center_lng = Column(DECIMAL(9, 6), nullable=True)

    # ✅ UPDATED: zone boundary polygon
    boundary = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)

    created_by = Column(VARCHAR(20), nullable=False, server_default="admin")
    created_on = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_by = Column(BigInteger, nullable=True)
    updated_on = Column(TIMESTAMP(timezone=True), nullable=True)
