from sqlalchemy import Column, BigInteger, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import ENUM
from app.models.base import Base
from app.schemas.enums import ApprovalStatusEnum, VehicleDocumentTypeEnum

class VehicleDocument(Base):
    __tablename__ = "vehicle_document"

    document_id = Column(BigInteger, primary_key=True, index=True)

    vehicle_id = Column(BigInteger, ForeignKey("vehicle.vehicle_id", ondelete="CASCADE"), nullable=False, index=True)

    document_type = Column(ENUM(VehicleDocumentTypeEnum, name="vehicle_document_type_enum"), nullable=False)

    file_url = Column(Text, nullable=False)

    verification_status = Column(
        ENUM(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        server_default="PENDING"
    )

    verified_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    verified_on = Column(TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
