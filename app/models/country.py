from sqlalchemy import Column, String, Text
from app.models.base import Base

class Country(Base):
    __tablename__ = "country"

    country_code = Column(String(2), primary_key=True)
    name = Column(Text, nullable=False)
    timezone = Column(Text, nullable=False)
    currency = Column(String(3), nullable=False)
    phone_code = Column(String(6), nullable=False)
