from sqlalchemy import Column, BigInteger, String, TIMESTAMP, ForeignKey, Enum, Text, func
from app.models.base import Base
from app.schemas.enums import ApprovalStatusEnum, FleetDocumentTypeEnum


class FleetDocument(Base):
    __tablename__ = "fleet_document"

    document_id = Column(BigInteger, primary_key=True, index=True)

    fleet_id = Column(
        BigInteger,
        ForeignKey("fleet.fleet_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ✅ ENUM document type (Postgres enum name must match)
    document_type = Column(
        Enum(FleetDocumentTypeEnum, name="fleet_document_type_enum"),
        nullable=False
    )

    file_url = Column(Text, nullable=False)
    document_number = Column(String(100), nullable=True)

    verification_status = Column(
        Enum(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        server_default="PENDING"
    )

    verified_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    verified_on = Column(TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
