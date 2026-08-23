"""Curated Nairobi place names for labeling coordinates in plain language.

Approximate area centers, not precise boundaries — good enough to tell a non-technical reader
"this cluster is near Mathare" instead of showing them a raw lat/lon pair. A building gets
labeled with the nearest area below only if it's within MAX_LABEL_DISTANCE_KM of it; otherwise
it falls back to a generic "Nairobi" label rather than guessing wrong.
"""
import math

NAIROBI_AREAS = {
    'Kasarani': (36.8969, -1.2296),
    'Mathare': (36.857, -1.259),
    'Kibera': (36.789, -1.313),
    'Mukuru': (36.870, -1.310),
    'Korogocho': (36.8817, -1.2447),
    'Dandora': (36.8961, -1.2436),
    'Kariobangi': (36.8814, -1.2597),
    'Huruma': (36.8622, -1.2649),
    'Ruaraka': (36.8875, -1.2431),
    'Githurai': (36.9020, -1.1874),
}

MAX_LABEL_DISTANCE_KM = 4.0


def _haversine_km(lon1, lat1, lon2, lat2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_area_name(lon, lat):
    """Nearest curated area name within MAX_LABEL_DISTANCE_KM, else 'Nairobi area'."""
    best_name, best_dist = None, float('inf')
    for name, (area_lon, area_lat) in NAIROBI_AREAS.items():
        d = _haversine_km(lon, lat, area_lon, area_lat)
        if d < best_dist:
            best_name, best_dist = name, d
    if best_dist <= MAX_LABEL_DISTANCE_KM:
        return best_name
    return 'Nairobi area'
