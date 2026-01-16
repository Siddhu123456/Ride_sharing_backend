from sqlalchemy import Column, BigInteger, Boolean, TIMESTAMP, Enum, ForeignKey, func
from app.models.base import Base
from app.schemas.enums import UserRoleEnum  # (or define enum locally)

class UserRole(Base):
    __tablename__ = "user_roles"

    user_role_id = Column(BigInteger, primary_key=True, index=True)

    user_id = Column(
        BigInteger,
        ForeignKey("app_user.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_role = Column(Enum(UserRoleEnum, name="user_role_enum"), nullable=False)

    is_active = Column(Boolean, default=True)

    assigned_on = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
