import requests

HEADERS = {
    "User-Agent": "RideSharingBackend/1.0"
}

def reverse_geocode(lat: float, lng: float) -> str | None:
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "json", "lat": lat, "lon": lng},
            headers=HEADERS,
            timeout=5
        )
        resp.raise_for_status()
        return resp.json().get("display_name")
    except Exception:
        return None
