from sqlalchemy import Column, BigInteger, String, Enum, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class AppUser(Base):
    __tablename__ = "app_user"

    user_id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)  # or Enum later
    phone = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)  # Email is required (NOT NULL)
    country_code = Column(String(2), ForeignKey("country.country_code"), nullable=False)  # Country code column added and required
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
