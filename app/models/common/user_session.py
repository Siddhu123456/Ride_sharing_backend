from sqlalchemy import Column, BigInteger, TIMESTAMP, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import Base
from app.schemas.enums import UserRoleEnum


class UserSession(Base):
    __tablename__ = "user_session"

    session_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    user_id = Column(
        BigInteger,
        ForeignKey("app_user.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    active_role = Column(Enum(UserRoleEnum, name="user_role_enum"), nullable=False)

    logged_in_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    logged_out_at = Column(TIMESTAMP(timezone=True), nullable=True)
