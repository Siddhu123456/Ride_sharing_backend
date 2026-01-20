from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.payment import Payment
from app.models.trip import Trip
from app.schemas.enums import PaymentStatusEnum


def create_payment_for_trip(db: Session, trip: Trip) -> Payment:
    # prevent duplicate payment rows
    existing = db.execute(
        select(Payment).where(Payment.trip_id == trip.trip_id)
    ).scalar_one_or_none()

    if existing:
        return existing

    payment = Payment(
        trip_id=trip.trip_id,
        amount=trip.fare_amount,
        currency="INR",          # you can take from tenant later
        payment_mode="OFFLINE",  # placeholder
        status=PaymentStatusEnum.PENDING
    )

    db.add(payment)
    db.flush()
    return payment
