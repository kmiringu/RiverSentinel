"""Riparian geometry & wide-radius comparison — reused across notebooks 05/07, scripts/, and app/."""
import ee


def get_river_geometry(boundary, search_radius=200, max_error=10):
    rivers = ee.FeatureCollection('WWF/HydroSHEDS/v1/FreeFlowingRivers').filterBounds(boundary)
    dist_to_river = rivers.distance(searchRadius=search_radius, maxError=max_error).clip(boundary)
    return rivers, dist_to_river


def get_all_features(fc, batch_size=4000):
    """Fetch every feature in `fc` as plain dicts, paginating around Earth Engine's ~5000-element
    getInfo() cap (hit for real: Kasarani's within-200m building set is 8,202 features — a single
    getInfo() call on it raises 'Collection query aborted after accumulating over 5000 elements').
    """
    n = fc.size().getInfo()
    features = []
    for start in range(0, n, batch_size):
        batch = ee.FeatureCollection(fc.toList(batch_size, start))
        features.extend(batch.getInfo()['features'])
    return features


def wide_radius_diff(builtup, riverside_mask, lon, lat, radius=1000):
    """Riverside (within riverside_mask) vs. surrounding built-up % within `radius` meters of a point.

    Returns (riverside_pct, surrounding_pct), each NaN if there aren't enough pixels on that side
    (e.g. no river within range, or the whole region falls on one side of the mask).
    """
    region = ee.Geometry.Point([lon, lat]).buffer(radius)
    grouped = builtup.rename('b').addBands(riverside_mask.rename('zone')).reduceRegion(
        reducer=ee.Reducer.mean().group(groupField=1, groupName='zone'),
        geometry=region, scale=10, maxPixels=1e9, bestEffort=True,
    ).getInfo()['groups']
    by_zone = {g['zone']: g['mean'] * 100 for g in grouped}
    return by_zone.get(1, float('nan')), by_zone.get(0, float('nan'))
