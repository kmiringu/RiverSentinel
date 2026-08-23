"""Consolidate key numbers from notebooks 03/05/06/07 into one JSON for the Streamlit app.

Only two things here are new Earth Engine work: rebuilding the 2024 classification (needed
anyway — every page's numbers depend on it) and the city-wide buffer-width sweep (cheap, three
group-reduceRegion calls over the whole city, same as notebook 05's code cell 5). Everything
else — grid-scan top hotspots, combined candidates, the named-hotspot cross-check — is derived
from data/processed/combined_riparian_hotspots.csv, which notebook 07 already exported; no need
to re-run the expensive 3016-cell grid scan just to summarize it.
"""
import csv
import json
import sys
from pathlib import Path

import ee

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

from acquisition import get_nairobi_boundary, get_sentinel2_composite
from classification import (
    build_feature_image, get_worldcover_builtup, sample_training_points,
    train_random_forest, classify_builtup,
)
from riparian import get_river_geometry

PROCESSED_DIR = REPO_ROOT / 'data' / 'processed'

ee.Initialize(project='solar-haven-349708')

nairobi = get_nairobi_boundary()
composite, scene_count = get_sentinel2_composite(
    nairobi, start_date='2024-06-01', end_date='2024-09-30', cloud_threshold=20
)
features = build_feature_image(composite)
worldcover_builtup = get_worldcover_builtup(nairobi)
train_samples, test_samples = sample_training_points(features, worldcover_builtup, nairobi)
classifier = train_random_forest(train_samples)
builtup = classify_builtup(features, classifier)
test_accuracy = test_samples.classify(classifier).errorMatrix(
    'builtup', 'classification'
).accuracy().getInfo()
print(f'Classification: {scene_count} scenes, {test_accuracy * 100:.1f}% held-out accuracy')

rivers, dist_to_river = get_river_geometry(nairobi)
river_count = rivers.size().getInfo()
river_length_km = rivers.aggregate_sum('LENGTH_KM').getInfo()

wdpa = ee.FeatureCollection('WCMC/WDPA/current/polygons')
park_fc = wdpa.filter(ee.Filter.And(ee.Filter.eq('NAME', 'Nairobi'), ee.Filter.gt('REP_AREA', 100)))
outside_park_mask = ee.Image().paint(park_fc, 1).unmask(0).eq(0)
builtup_outside_park = builtup.updateMask(outside_park_mask)

city_frac = builtup_outside_park.rename('b').reduceRegion(
    reducer=ee.Reducer.mean(), geometry=nairobi, scale=10, maxPixels=1e9, bestEffort=True
).getInfo()['b'] * 100
print(f'City-wide built-up (excl. park): {city_frac:.1f}%')

buffer_sweep = []
for buf in [30, 50, 100]:
    zone = dist_to_river.lte(buf)
    grouped = builtup_outside_park.rename('b').addBands(zone.rename('zone')).reduceRegion(
        reducer=ee.Reducer.mean().group(groupField=1, groupName='zone'),
        geometry=nairobi, scale=10, maxPixels=1e9, bestEffort=True,
    ).getInfo()['groups']
    by_zone = {g['zone']: g['mean'] * 100 for g in grouped}
    buffer_sweep.append({
        'buffer_m': buf,
        'in_buffer_pct': by_zone.get(1),
        'rest_of_city_pct': by_zone.get(0),
    })
    print(f'  buffer {buf}m: in-buffer {by_zone.get(1):.1f}%, rest-of-city {by_zone.get(0):.1f}%')

candidates_path = PROCESSED_DIR / 'combined_riparian_hotspots.csv'
with open(candidates_path) as f:
    candidates = []
    numeric_fields = ['lon', 'lat', 'riverside_pct', 'rest_pct', 'diff_pp',
                       'wide_riverside_pct', 'wide_rest_pct', 'wide_diff_pp', 'best_diff_pp']
    for row in csv.DictReader(f):
        for k in numeric_fields:
            row[k] = float(row[k])
        candidates.append(row)

narrow_top15 = sorted(
    (c for c in candidates if 'narrow' in c['source']), key=lambda r: -r['diff_pp']
)[:15]
saturated_top15 = sorted(
    (c for c in candidates if 'saturated' in c['source']), key=lambda r: -r['wide_diff_pp']
)[:15]

named_hotspots = {'Mathare': (36.857, -1.259), 'Kibera': (36.789, -1.313), 'Mukuru': (36.870, -1.310)}


def nearest_candidate(lon, lat):
    return min(candidates, key=lambda r: (r['lon'] - lon) ** 2 + (r['lat'] - lat) ** 2)


cross_check = []
for name, (lon, lat) in named_hotspots.items():
    match = nearest_candidate(lon, lat)
    cross_check.append({
        'name': name,
        'source': match['source'],
        'narrow_diff_pp': match['diff_pp'],
        'wide_diff_pp': match['wide_diff_pp'],
    })

summary = {
    'classification': {'scene_count': scene_count, 'held_out_accuracy_pct': test_accuracy * 100},
    'rivers': {'reach_count': river_count, 'total_length_km': river_length_km},
    'city_wide': {'builtup_pct_excl_park': city_frac, 'buffer_sweep': buffer_sweep},
    'named_hotspot_cross_check': cross_check,
    'grid_scan': {
        'total_cells': 3016,
        'cells_compared': 578,
        'min_pixels': 20,
        'grid_size_m': 500,
        'top15_narrow_edge': narrow_top15,
    },
    'combined_report': {
        'candidate_count': len(candidates),
        'top15_saturated': saturated_top15,
    },
}

buildings_path = PROCESSED_DIR / 'building_encroachment_summary.json'
if buildings_path.exists():
    with open(buildings_path) as f:
        summary['buildings'] = json.load(f)

out_path = PROCESSED_DIR / 'pipeline_summary.json'
with open(out_path, 'w') as f:
    json.dump(summary, f, indent=2)
print(f'Saved {out_path}')
