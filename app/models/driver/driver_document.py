from sqlalchemy import Column, BigInteger, String, Text, Date, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.schema import UniqueConstraint
from app.models.base import Base
from app.schemas.enums import ApprovalStatusEnum, DriverDocumentTypeEnum


class DriverDocument(Base):
    __tablename__ = "driver_document"

    document_id = Column(BigInteger, primary_key=True, index=True)

    driver_id = Column(BigInteger, ForeignKey("app_user.user_id", ondelete="CASCADE"), nullable=False, index=True)

    document_type = Column(
        ENUM(DriverDocumentTypeEnum, name="driver_document_type_enum"),
        nullable=False
    )

    file_url = Column(Text, nullable=False)
    document_number = Column(String(100), nullable=True)

    verification_status = Column(
        ENUM(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        server_default="PENDING"
    )

    verified_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    verified_on = Column(TIMESTAMP(timezone=True), nullable=True)

    expiry_date = Column(Date, nullable=True)

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("driver_id", "document_type", name="uq_driver_document"),
    )
