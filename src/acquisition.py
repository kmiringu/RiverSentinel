"""Nairobi imagery acquisition — proven in notebooks/01_nairobi_imagery_acquisition.ipynb."""
import ee


def get_nairobi_boundary():
    admin2 = ee.FeatureCollection('FAO/GAUL/2015/level2')
    nairobi_fc = admin2.filter(
        ee.Filter.And(
            ee.Filter.eq('ADM0_NAME', 'Kenya'),
            ee.Filter.eq('ADM1_NAME', 'Nairobi'),
        )
    )
    return nairobi_fc.geometry()


def get_sentinel2_composite(boundary, start_date, end_date, cloud_threshold=20):
    s2_filtered = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(boundary)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_threshold))
    )
    scene_count = s2_filtered.size().getInfo()
    composite = s2_filtered.median().clip(boundary)
    return composite, scene_count
