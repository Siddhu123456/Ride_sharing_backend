from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Enum,
    Boolean,
    TIMESTAMP,
    func,
    ForeignKey
)
from app.models.base import Base

class AppUser(Base):
    __tablename__ = "app_user"

    user_id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    gender = Column(String)  # keep simple for now
    phone = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True)
    status = Column(String, default="ACTIVE")
    created_on = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )


class UserAuth(Base):
    __tablename__ = "user_auth"

    user_id = Column(
        BigInteger,
        ForeignKey("app_user.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    password_hash = Column(String, nullable=False)
    is_locked = Column(Boolean, default=False)

