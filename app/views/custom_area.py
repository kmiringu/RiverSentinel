import math
import sys
from pathlib import Path

import ee
import folium
import pandas as pd
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'src'))
from acquisition import get_nairobi_boundary
from riparian import get_all_features, get_river_geometry
from named_areas import nearest_area_name
from utils import load_summary

MAX_AREA_KM2 = 30

st.title('📐 Draw Your Own Area')
st.markdown('''
Kasarani is where we had a real number to check our work against, but the same method works
anywhere in Nairobi. Draw a rectangle or circle on the map below, then generate a report for
exactly that area — no need to wait for us to add it as a named case study.
''')


@st.cache_resource(show_spinner='Loading the river network (first visit only)...')
def get_dist_to_river():
    ee.Initialize(project='solar-haven-349708')
    nairobi = get_nairobi_boundary()
    _, dist_to_river = get_river_geometry(nairobi)
    return nairobi, dist_to_river


nairobi, dist_to_river = get_dist_to_river()

m = folium.Map(location=[-1.29, 36.868], zoom_start=11, tiles='CartoDB positron', scrollWheelZoom=False)
Draw(
    export=False,
    draw_options={'polyline': False, 'polygon': False, 'marker': False, 'circlemarker': False,
                  'rectangle': {'shapeOptions': {'color': '#CC0000'}},
                  'circle': {'shapeOptions': {'color': '#CC0000'}}},
    edit_options={'edit': True, 'remove': True},
).add_to(m)

map_state = st_folium(m, use_container_width=True, height=500, key='custom_area_map',
                       returned_objects=['last_active_drawing'])

drawing = map_state.get('last_active_drawing') if map_state else None

if not drawing:
    st.info('Draw a rectangle or circle on the map, then click "Generate Report" below.')
    st.stop()


def drawing_to_ee_geometry_and_area(drawing):
    geom = drawing['geometry']
    props = drawing.get('properties', {})
    if geom['type'] == 'Point' and 'radius' in props:
        lon, lat = geom['coordinates']
        radius_m = props['radius']
        ee_geom = ee.Geometry.Point([lon, lat]).buffer(radius_m)
        area_km2 = math.pi * (radius_m / 1000) ** 2
        return ee_geom, area_km2
    if geom['type'] == 'Polygon':
        coords = geom['coordinates']
        ee_geom = ee.Geometry.Polygon(coords)
        lons = [c[0] for c in coords[0]]
        lats = [c[1] for c in coords[0]]
        lat_mid = sum(lats) / len(lats)
        width_km = (max(lons) - min(lons)) * 111 * math.cos(math.radians(lat_mid))
        height_km = (max(lats) - min(lats)) * 111
        area_km2 = width_km * height_km
        return ee_geom, area_km2
    return None, None


ee_geom, area_km2 = drawing_to_ee_geometry_and_area(drawing)

if ee_geom is None:
    st.error('Could not read that shape — try a rectangle or circle instead.')
    st.stop()

st.caption(f'Selected area: about {area_km2:.1f} km²')

if area_km2 > MAX_AREA_KM2:
    st.error(
        f'That area is about {area_km2:.0f} km² — larger than the {MAX_AREA_KM2} km² this page '
        f'can process in one go (Kasarani, our largest tested case study, is about 28 km²). '
        f'Draw a smaller area, or check the Technical Methodology pages for the city-wide scan.'
    )
    st.stop()

calibrated_m = load_summary().get('buildings', {}).get('kasarani', {}).get('calibrated_distance_m', 18)
dist_m = st.slider('Flag buildings within this many meters of a river', min_value=5, max_value=100,
                    value=calibrated_m, step=1)

if st.button('Generate Report', type='primary'):
    with st.spinner(f'Screening buildings in ~{area_km2:.1f} km²... this can take up to a minute.'):
        open_buildings = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons')
        area_buildings = open_buildings.filterBounds(ee_geom).filter(ee.Filter.gte('confidence', 0.7))
        total = area_buildings.size().getInfo()

        sampled = dist_to_river.reduceRegions(collection=area_buildings, reducer=ee.Reducer.first(), scale=10)
        sampled = sampled.filter(ee.Filter.notNull(['first']))
        near_river = sampled.size().getInfo()
        flagged = sampled.filter(ee.Filter.lte('first', dist_m))
        flagged_info = get_all_features(flagged)

    rows = []
    for f in flagged_info:
        props = f['properties']
        lon, lat = props['longitude_latitude']['coordinates']
        rows.append({
            'lon': lon, 'lat': lat, 'confidence': props['confidence'],
            'area_m2': props['area_in_meters'], 'distance_to_river_m': props['first'],
        })

    centroid = ee_geom.centroid(1).coordinates().getInfo()
    area_name = nearest_area_name(centroid[0], centroid[1])

    st.success(f'Done — this area is closest to **{area_name}**.')
    st.markdown(f'''
    ### Report: area near {area_name}
    We checked **{total:,} buildings** in the area you drew. **{near_river:,}** of them are close
    enough to a river to measure a distance at all. At the **{dist_m}m** screening distance,
    **{len(rows):,} buildings** are flagged as potentially encroaching.
    ''')

    col1, col2, col3 = st.columns(3)
    col1.metric('Buildings checked', f'{total:,}')
    col2.metric('Near a river (within 200m)', f'{near_river:,}')
    col3.metric(f'Flagged (within {dist_m}m)', f'{len(rows):,}')

    if rows:
        result_map = folium.Map(location=[centroid[1], centroid[0]], zoom_start=14,
                                 tiles='CartoDB positron', scrollWheelZoom=False)
        for r in rows:
            folium.CircleMarker(
                location=[r['lat'], r['lon']], radius=4, color='#CC0000', weight=1,
                fill=True, fill_color='#CC0000', fill_opacity=0.8,
                popup=folium.Popup(f"{r['distance_to_river_m']:.0f}m from the river", max_width=180),
            ).add_to(result_map)
        st_folium(result_map, use_container_width=True, height=450, key='custom_area_result_map',
                  returned_objects=[])

        df = pd.DataFrame(rows).sort_values('distance_to_river_m')
        st.download_button(
            label=f'⬇️ Download this list ({len(rows):,} buildings, CSV)',
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f'{area_name.replace(" ", "_").lower()}_encroaching_buildings.csv',
            mime='text/csv',
        )
        with st.expander(f'View as a table ({len(rows):,} rows)'):
            st.dataframe(
                df.rename(columns={'lat': 'Latitude', 'lon': 'Longitude',
                                    'distance_to_river_m': 'Distance to river (m)',
                                    'area_m2': 'Building size (m²)', 'confidence': 'Detection confidence'}),
                hide_index=True, use_container_width=True, height=300,
            )
    else:
        st.info('No buildings flagged at this distance in the selected area.')

    st.caption('Same caveats as the Kasarani report apply here — this is a candidate list for '
               'field verification, not a confirmed one. See Encroaching Buildings for details.')
