from sqlalchemy import Column, BigInteger, Integer, Text, ForeignKey, TIMESTAMP, func
from app.models.base import Base


class TripRating(Base):
    __tablename__ = "trip_rating"

    rating_id = Column(BigInteger, primary_key=True)

    trip_id = Column(
        BigInteger,
        ForeignKey("trip.trip_id"),
        nullable=False,
        index=True
    )

    rater_id = Column(
        BigInteger,
        ForeignKey("app_user.user_id"),
        nullable=False
    )

    ratee_id = Column(
        BigInteger,
        ForeignKey("app_user.user_id"),
        nullable=False
    )

    rating = Column(Integer, nullable=False)
    comment = Column(Text)

    created_on = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
