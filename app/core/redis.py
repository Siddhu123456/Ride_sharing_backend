import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

DRIVER_LOCATIONS_KEY = "drivers:locations"
