from sqlalchemy import (
    Column,
    BigInteger,
    Numeric,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.dialects.postgresql import ENUM
from app.models.base import Base
from app.schemas.enums import VehicleCategoryEnum


class FareConfig(Base):
    __tablename__ = "fare_config"

    fare_config_id = Column(BigInteger, primary_key=True)

    tenant_id = Column(
        BigInteger,
        ForeignKey("tenant.tenant_id"),
        nullable=False,
        index=True
    )

    city_id = Column(
        BigInteger,
        ForeignKey("city.city_id"),
        nullable=False,
        index=True
    )

    vehicle_category = Column(
        ENUM(VehicleCategoryEnum, name="vehicle_category_enum"),
        nullable=False
    )

    base_fare = Column(Numeric(10, 2), nullable=False)
    per_km_rate = Column(Numeric(10, 2), nullable=False)
    per_min_rate = Column(Numeric(10, 2), nullable=False)

    minimum_fare = Column(Numeric(10, 2))
    platform_commission_percent = Column(Numeric(5, 2))

    is_active = Column(Boolean, nullable=False, server_default="true")

    effective_from = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    effective_to = Column(TIMESTAMP(timezone=True))

    created_on = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    updated_on = Column(TIMESTAMP(timezone=True))

    __table_args__ = (
        # ⚠️ keep this ONLY if you used Option A
        UniqueConstraint(
            "city_id",
            "vehicle_category",
            name="uq_fare_config_city_vehicle"
        ),
    )
