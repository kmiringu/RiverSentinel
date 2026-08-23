import sys
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from named_areas import nearest_area_name
from utils import load_buildings, load_summary

st.title('🏠 Encroaching Buildings')

building_summary = load_summary().get('buildings')
if building_summary is None:
    st.warning('Run `notebooks/08_building_level_encroachment.ipynb` and re-run `scripts/export_pipeline_summary.py` to populate this page.')
    st.stop()

kasarani = building_summary['kasarani']
other = building_summary['other_hotspots_top15']
calibrated_m = kasarani['calibrated_distance_m']
pamoja_count = kasarani['pamoja_trust_reported_count']

st.markdown('''
Every point on the map below is a real building. Use the slider to choose how close counts as
"too close to the river" — we've set it to the distance that best matches Pamoja Trust's own
count from walking Kasarani by hand, but you can widen or narrow it to see how the list changes.
''')

dist_m = st.slider(
    'Flag buildings within this many meters of a river',
    min_value=5, max_value=100, value=calibrated_m, step=1,
)
if dist_m == calibrated_m:
    st.caption(f"✓ This matches our calibration against Pamoja Trust's reported count (~{pamoja_count:,}).")

kasarani_scored = load_buildings('kasarani_buildings_scored.csv')
kasarani_flagged = [b for b in kasarani_scored if b['distance_to_river_m'] <= dist_m]

col1, col2, col3 = st.columns(3)
col1.metric('Buildings flagged', f"{len(kasarani_flagged):,}")
col2.metric("Pamoja Trust's field count", f"~{pamoja_count:,}")
col3.metric('Difference', f"{len(kasarani_flagged) - pamoja_count:+,}")

m = folium.Map(location=[-1.2296, 36.8969], zoom_start=13, tiles='CartoDB positron', scrollWheelZoom=False)
for b in kasarani_flagged:
    folium.CircleMarker(
        location=[b['lat'], b['lon']],
        radius=3,
        color='#CC0000',
        weight=1,
        fill=True,
        fill_color='#CC0000',
        fill_opacity=0.8,
        popup=folium.Popup(
            f"Near {nearest_area_name(b['lon'], b['lat'])}<br>"
            f"{b['distance_to_river_m']:.0f}m from the river",
            max_width=200,
        ),
    ).add_to(m)
st_folium(m, use_container_width=True, height=500, returned_objects=[])
st.caption(f"Kasarani, Nairobi — {len(kasarani_flagged):,} buildings within {dist_m}m of a river.")

df = pd.DataFrame(kasarani_flagged)
if not df.empty:
    df['Area'] = [nearest_area_name(b['lon'], b['lat']) for b in kasarani_flagged]
csv_bytes = df.to_csv(index=False).encode('utf-8') if not df.empty else b''
st.download_button(
    label=f'⬇️ Download the list ({len(kasarani_flagged):,} buildings, CSV)',
    data=csv_bytes,
    file_name=f'kasarani_encroaching_buildings_{dist_m}m.csv',
    mime='text/csv',
    disabled=df.empty,
)

with st.expander(f'View as a table ({len(kasarani_flagged):,} rows)'):
    if not df.empty:
        st.dataframe(
            df.sort_values('distance_to_river_m').rename(columns={
                'lat': 'Latitude', 'lon': 'Longitude',
                'distance_to_river_m': 'Distance to river (m)',
                'area_m2': 'Building size (m²)', 'confidence': 'Detection confidence',
            })[['Area', 'Latitude', 'Longitude', 'Distance to river (m)', 'Building size (m²)', 'Detection confidence']],
            hide_index=True, use_container_width=True, height=300,
        )
    else:
        st.caption('No buildings at this distance.')

st.divider()
st.subheader('How we picked the default distance')
st.markdown(f'''
There's no single "correct" distance that defines encroachment — it depends on the river, local
regulation, and judgment call. Rather than guess, we checked several distances against the one
number we actually have from real fieldwork: Pamoja Trust's reported count of about
**{pamoja_count:,}** buildings in Kasarani.
''')

sweep_df = pd.DataFrame([
    {'Distance from river': f'{d}m', 'Buildings flagged': n}
    for d, n in sorted(kasarani['calibration_sweep'].items(), key=lambda kv: int(kv[0]))
])
st.dataframe(sweep_df, hide_index=True, use_container_width=True)
st.caption(f"{calibrated_m} meters landed closest to Pamoja Trust's count — a gap of "
           f"{kasarani['encroaching_count'] - pamoja_count} buildings, versus the "
           f"{kasarani['buffer_sweep']['30'] - pamoja_count}-building gap our first, unchecked "
           f"guess of 30m produced.")

st.divider()
st.subheader('Other areas worth checking')
st.markdown(f'''
Kasarani is where we had a real number to check our work against, but the same method works
anywhere. We also scanned 15 other locations across Nairobi that an earlier, city-wide pass had
already flagged as unusual — screened {other['buildings_screened']:,} buildings there.
''')

other_scored = load_buildings('other_hotspots_buildings_scored.csv')
other_flagged = [b for b in other_scored if b['distance_to_river_m'] <= dist_m]
st.metric(f'Buildings flagged within {dist_m}m', f"{len(other_flagged):,}")

m2 = folium.Map(location=[-1.29, 36.868], zoom_start=11, tiles='CartoDB positron', scrollWheelZoom=False)
for b in other_flagged:
    folium.CircleMarker(
        location=[b['lat'], b['lon']],
        radius=4,
        color='#CC0000',
        weight=1,
        fill=True,
        fill_color='#CC0000',
        fill_opacity=0.8,
        popup=folium.Popup(
            f"Near {nearest_area_name(b['lon'], b['lat'])}<br>{b['distance_to_river_m']:.0f}m from the river",
            max_width=200,
        ),
    ).add_to(m2)
st_folium(m2, use_container_width=True, height=450, returned_objects=[])
st.caption('This is a partial scan of the city, not a complete one — see limitations below.')

other_df = pd.DataFrame(other_flagged)
if not other_df.empty:
    other_df['Area'] = [nearest_area_name(b['lon'], b['lat']) for b in other_flagged]
other_csv_bytes = other_df.to_csv(index=False).encode('utf-8') if not other_df.empty else b''
st.download_button(
    label=f'⬇️ Download this list ({len(other_flagged):,} buildings, CSV)',
    data=other_csv_bytes,
    file_name=f'other_areas_encroaching_buildings_{dist_m}m.csv',
    mime='text/csv',
    disabled=other_df.empty,
)

with st.expander('Limitations — what this tool can\'t tell you'):
    st.markdown('''
    - **This finds candidates, not confirmed cases.** Every flagged building still needs a field
      visit before any action is taken.
    - **Matching Pamoja Trust's total doesn't mean matching their exact list.** We don't have
      their building-by-building results to check against — only their reported total. It's
      possible some flagged buildings aren't real encroachments, and some real ones were missed.
    - **This isn't the whole city.** Outside Kasarani and the 15 other checked locations, we
      haven't screened every building in Nairobi yet — that would need more computing time than
      this project has used so far. Use the "Draw Your Own Area" page to check a specific
      location we haven't already covered.
    - **Area names are approximate.** Locations are labeled by the nearest of a small, hand-picked
      list of known Nairobi areas — not an official boundary lookup, and unlabeled areas just say
      "Nairobi area."
    - **This is a single snapshot (2024).** It shows where buildings sit today, not whether
      encroachment is getting worse over time.
    - Full technical detail — data sources, exact method, every number — is under **Technical
      Methodology** in the sidebar.
    ''')
