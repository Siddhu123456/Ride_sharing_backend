from app.models.trip import Trip
from app.models.trip_fare_breakdown import TripFareBreakdown


def compute_fare_simple(trip: Trip, distance_km: float | None, duration_minutes: int | None):
    """
    ✅ SIMPLE TEMP FARE:
    base_fare = 30
    distance_fare = 10/km
    time_fare = 1/min
    tax = 5%
    """

    base_fare = 30.0
    per_km = 10.0
    per_min = 1.0

    d = float(distance_km or 0)
    t = float(duration_minutes or 0)

    distance_fare = d * per_km
    time_fare = t * per_min

    surge_amount = 0.0
    discount_amount = 0.0

    subtotal = base_fare + distance_fare + time_fare + surge_amount - discount_amount
    tax_amount = subtotal * 0.05

    final_fare = subtotal + tax_amount

    return {
        "base_fare": base_fare,
        "distance_fare": distance_fare,
        "time_fare": time_fare,
        "surge_amount": surge_amount,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "final_fare": final_fare,
    }


def insert_fare_breakdown(db, trip_id: int, data: dict) -> TripFareBreakdown:
    row = TripFareBreakdown(
        trip_id=trip_id,
        base_fare=data["base_fare"],
        distance_fare=data["distance_fare"],
        time_fare=data["time_fare"],
        surge_amount=data["surge_amount"],
        discount_amount=data["discount_amount"],
        tax_amount=data["tax_amount"],
        final_fare=data["final_fare"],
    )
    db.add(row)
    db.flush()
    return row
