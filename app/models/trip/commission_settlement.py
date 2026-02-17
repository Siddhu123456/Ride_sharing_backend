from sqlalchemy import Column, BigInteger, Numeric, Enum, TIMESTAMP, ForeignKey, func
from app.models.base import Base
from app.schemas.enums import SettlementStatusEnum


class CommissionSettlement(Base):
    __tablename__ = "commission_settlement"

    settlement_id = Column(BigInteger, primary_key=True, index=True)

    tenant_id = Column(
        BigInteger,
        ForeignKey("tenant.tenant_id"),
        nullable=False
    )

    fleet_id = Column(
        BigInteger,
        ForeignKey("fleet.fleet_id"),
        nullable=False
    )

    total_commission = Column(Numeric(12, 2), nullable=False)

    status = Column(
        Enum(
            SettlementStatusEnum,
            name="settlement_status_enum",
            create_type=False
        ),
        nullable=False,
        server_default="PENDING"
    )

    created_on = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    paid_on = Column(TIMESTAMP(timezone=True))
