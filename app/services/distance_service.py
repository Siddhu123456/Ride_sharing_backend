from geopy.distance import geodesic

def calculate_distance_km(lat1, lng1, lat2, lng2):
    return geodesic((lat1, lng1), (lat2, lng2)).km
