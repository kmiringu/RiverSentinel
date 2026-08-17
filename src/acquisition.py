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


def _mask_s2_clouds(image):
    """Per-pixel cloud/shadow mask via the SCL band (3=shadow, 8/9=cloud, 10=cirrus).

    The scene-level CLOUDY_PIXEL_PERCENTAGE filter alone lets contaminated pixels through
    within an otherwise-accepted scene; those survive a median composite when few scenes
    contribute (notebook 04 found this corrupting a low-scene-count year, not the well-covered
    2024 composite where it went unnoticed).
    """
    scl = image.select('SCL')
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)


def get_sentinel2_composite(boundary, start_date, end_date, cloud_threshold=20):
    s2_filtered = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(boundary)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_threshold))
        .map(_mask_s2_clouds)
    )
    scene_count = s2_filtered.size().getInfo()
    composite = s2_filtered.median().clip(boundary)
    return composite, scene_count
