from pydantic import BaseModel


class FareBreakdownResponse(BaseModel):
    trip_id: int
    base_fare: float
    distance_fare: float
    time_fare: float
    surge_amount: float
    tax_amount: float
    discount_amount: float
    final_fare: float
