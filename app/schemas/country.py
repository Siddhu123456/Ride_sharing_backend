from pydantic import BaseModel, ConfigDict

class CountryResponse(BaseModel):
    country_code: str
    name: str
    default_timezone: str
    default_currency: str
    phone_code: str

    model_config = ConfigDict(from_attributes=True)
