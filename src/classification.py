"""Built-up classification via Random Forest — proven in notebooks/03_random_forest_classification.ipynb."""
import ee

BANDS = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
FEATURE_NAMES = BANDS + ['NDVI', 'NDBI']


def build_feature_image(composite):
    ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI')
    return composite.select(BANDS).addBands(ndvi).addBands(ndbi)


def get_worldcover_builtup(boundary):
    worldcover = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map').clip(boundary)
    return worldcover.eq(50).rename('builtup')


def sample_training_points(feature_image, worldcover_builtup, boundary, num_points=1500, seed=42):
    training_image = feature_image.addBands(worldcover_builtup)
    samples = training_image.stratifiedSample(
        numPoints=num_points,
        classBand='builtup',
        region=boundary,
        scale=10,
        seed=seed,
        geometries=False,
    )
    samples = samples.randomColumn('split', seed=seed)
    train_samples = samples.filter(ee.Filter.lt('split', 0.7))
    test_samples = samples.filter(ee.Filter.gte('split', 0.7))
    return train_samples, test_samples


def train_random_forest(train_samples, num_trees=100, seed=42):
    return ee.Classifier.smileRandomForest(numberOfTrees=num_trees, seed=seed).train(
        features=train_samples,
        classProperty='builtup',
        inputProperties=FEATURE_NAMES,
    )


def classify_builtup(feature_image, classifier):
    return feature_image.classify(classifier).rename('builtup')


def normalize_to_reference(image, reference_image, boundary, bands=BANDS, scale=30):
    """Linear (mean/stdDev) histogram match of `image`'s bands onto `reference_image`.

    Needed before applying one classifier across composites from different years — see
    notebooks/04_change_detection.ipynb. Composites from different dates carry a systematic
    whole-scene brightness offset (different atmospheric conditions, sun angle, scene mix) large
    enough to fool a classifier trained on absolute reflectance values into spurious change. This
    corrects the first-order (mean/spread) mismatch per band over `boundary`; it does not correct
    non-stationary or non-linear differences, so residual noise should still be sanity-checked
    (e.g. a "reverted" class fraction that should be near zero).
    """
    stats_ref = reference_image.select(bands).reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=boundary, scale=scale, maxPixels=1e9, bestEffort=True,
    ).getInfo()
    stats_img = image.select(bands).reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=boundary, scale=scale, maxPixels=1e9, bestEffort=True,
    ).getInfo()

    normalized = []
    for b in bands:
        mean_img, std_img = stats_img[f'{b}_mean'], stats_img[f'{b}_stdDev']
        mean_ref, std_ref = stats_ref[f'{b}_mean'], stats_ref[f'{b}_stdDev']
        band = (
            image.select(b)
            .subtract(mean_img)
            .divide(std_img)
            .multiply(std_ref)
            .add(mean_ref)
            .rename(b)
        )
        normalized.append(band)
    return ee.Image.cat(normalized)
