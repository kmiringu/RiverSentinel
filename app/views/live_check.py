import math
import sys
from pathlib import Path

import ee
import folium
import streamlit as st
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'src'))
from acquisition import get_nairobi_boundary, get_sentinel2_composite
from classification import (
    build_feature_image, classify_builtup, get_worldcover_builtup,
    sample_training_points, train_random_forest,
)
from riparian import get_river_geometry, wide_radius_diff

st.title('📍 Live Point Check')

st.markdown('''
Click anywhere on the map to run a **live** Earth Engine query — riverside (within 30m of the
nearest river) built-up fraction vs. the surrounding 1km, computed on demand rather than read
from a precomputed table. Same method as the Combined Hotspot Report's wide-radius pass, reused
here via `src/riparian.py` instead of duplicated.

First load rebuilds the 2024 classification (~30-60s); it's cached after that, so later clicks
only pay for the query itself.
''')


@st.cache_resource(show_spinner='Building 2024 classification (first load only)...')
def get_classification():
    ee.Initialize(project='solar-haven-349708')
    nairobi = get_nairobi_boundary()
    composite, _ = get_sentinel2_composite(
        nairobi, start_date='2024-06-01', end_date='2024-09-30', cloud_threshold=20
    )
    features = build_feature_image(composite)
    worldcover_builtup = get_worldcover_builtup(nairobi)
    train_samples, _ = sample_training_points(features, worldcover_builtup, nairobi)
    classifier = train_random_forest(train_samples)
    builtup = classify_builtup(features, classifier)
    # search_radius wider than the 200m used elsewhere in the pipeline: notebooks 05/06/07 only
    # ever queried points already known to sit near a river, where the default was never tested
    # against arbitrary locations. A live "click anywhere" feature needs dist_to_river defined
    # much further out, or most clicks land in undefined territory and report "no river" when
    # the real answer is just "the nearest river is 200-2000m away, not truly out of range."
    _, dist_to_river = get_river_geometry(nairobi, search_radius=5000)
    riverside_mask = dist_to_river.lte(30)
    return builtup, riverside_mask


builtup, riverside_mask = get_classification()

m = folium.Map(location=[-1.29, 36.868], zoom_start=11, tiles='CartoDB positron', scrollWheelZoom=False)
map_state = st_folium(m, height=500, use_container_width=True, key='live_check_map')

if map_state and map_state.get('last_clicked'):
    lat = map_state['last_clicked']['lat']
    lon = map_state['last_clicked']['lng']
    st.write(f'Checking **({lon:.4f}, {lat:.4f})**...')
    with st.spinner('Running live Earth Engine query...'):
        riverside_pct, surrounding_pct = wide_radius_diff(builtup, riverside_mask, lon, lat)

    if math.isnan(riverside_pct) or math.isnan(surrounding_pct):
        st.error(
            "No river within range of this point, or not enough pixels on one side to compare "
            "— try clicking closer to a mapped river reach within Nairobi."
        )
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric('Riverside (30m) built-up %', f'{riverside_pct:.1f}%')
        col2.metric('Surrounding 1km built-up %', f'{surrounding_pct:.1f}%')
        col3.metric('Diff', f'{riverside_pct - surrounding_pct:+.1f}pp')
else:
    st.caption('Click the map above to check a location.')
