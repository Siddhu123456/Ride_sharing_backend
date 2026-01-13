from pydantic import BaseModel

class CountryResponse(BaseModel):
    country_code: str
    name: str
    timezone: str
    currency: str
    phone_code: str

    class Config:
        from_attributes = True   # ✅ for SQLAlchemy
