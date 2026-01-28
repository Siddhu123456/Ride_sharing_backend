from sqlalchemy import (
    Column,
    BigInteger,
    Enum as PgEnum,
    TIMESTAMP,
    DECIMAL,
    ForeignKey,
    func
)
from app.models.base import Base
from app.schemas.enums import DriverShiftStatusEnum


class DriverShift(Base):
    __tablename__ = "driver_shift"

    shift_id = Column(BigInteger, primary_key=True, index=True)

    driver_id = Column(
        BigInteger,
        ForeignKey("app_user.user_id", ondelete="CASCADE"),
        nullable=False
    )

    tenant_id = Column(
        BigInteger,
        ForeignKey("tenant.tenant_id", ondelete="CASCADE"),
        nullable=False
    )

    vehicle_id = Column(
        BigInteger,
        ForeignKey("vehicle.vehicle_id"),
        nullable=True
    )

    status = Column(
        PgEnum(
            DriverShiftStatusEnum,
            name="driver_shift_status_enum",
            create_type=False  # IMPORTANT: enum already exists in DB
        ),
        nullable=False,
        default=DriverShiftStatusEnum.ONLINE
    )

    started_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    expected_end_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    ended_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    last_latitude = Column(DECIMAL(9, 6), nullable=True)
    last_longitude = Column(DECIMAL(9, 6), nullable=True)
