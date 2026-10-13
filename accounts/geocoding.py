"""
Location helpers for FoodMitra.

geocode_address()  -> turns a text address into (latitude, longitude)
                       using OpenStreetMap's free Nominatim service.
                       No API key needed, but it's rate-limited to
                       ~1 request/second per their usage policy, so it's
                       only called at registration time / one-off backfill,
                       never on every page load.

haversine_km()      -> straight-line distance in km between two
                        lat/long points. Pure Python, no external calls,
                        safe to run on every menu page load.
"""
import re
import time
import requests
from math import radians, sin, cos, sqrt, atan2


def _try_geocode_query(query):
    """Single Nominatim lookup. Returns (lat, lng) or (None, None)."""
    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': query,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'in',  # bias results to India
            },
            headers={
                # Nominatim's usage policy requires a real identifying
                # User-Agent - requests without one get blocked.
                'User-Agent': 'FoodMitra/1.0 (support@foodmitra.in)'
            },
            timeout=5,
        )
        results = response.json()
        if results:
            return float(results[0]['lat']), float(results[0]['lon'])
    except Exception:
        pass
    return None, None


def geocode_address(address):
    """
    Returns (latitude, longitude) as floats, or (None, None) if the
    address couldn't be geocoded at all. Never raises - callers can
    always safely unpack the result.

    Hyper-specific addresses (house/plot numbers, small layout names)
    often aren't in Nominatim's free index for smaller Indian localities,
    so this tries progressively simpler versions of the address until
    one matches - full address first, then with the house number/plot
    stripped, then just the last one or two components (area/city).
    This trades some precision for reliably finding *something* close
    enough for a 5km radius check.
    """
    if not address or not address.strip():
        return None, None

    # Build a list of query variants, most specific first
    variants = [address]

    # Strip a leading house/plot number like "#45 " or "12/3 "
    stripped = re.sub(r'^[#\d/\-]+\s*', '', address).strip()
    if stripped and stripped != address:
        variants.append(stripped)

    # Try just the last 2 comma-separated parts (e.g. "RR Nagar, Mysore")
    parts = [p.strip() for p in address.split(',') if p.strip()]
    if len(parts) >= 2:
        variants.append(', '.join(parts[-2:]))

    # Last resort: just the final part (usually the city)
    if len(parts) >= 1:
        variants.append(parts[-1])

    for i, query in enumerate(variants):
        lat, lng = _try_geocode_query(query)
        if lat is not None:
            return lat, lng
        if i < len(variants) - 1:
            time.sleep(1)  # stay within Nominatim's rate limit between retries

    return None, None


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Distance in kilometers between two lat/long points.
    """
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c