import sys
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import image_path, load_candidates, load_summary

st.title('🎯 Combined Riparian Hotspot Report')

summary = load_summary()
candidates = load_candidates()

st.markdown(f'''
Merges the two prior methods instead of picking one, per the grid scan's own conclusion. Grid
cells are flagged two ways: **narrow-edge** (sharp local within-cell contrast) or **saturated**
(both sides already highly built-up — the Kibera blind spot), then only that merged candidate set
({summary['combined_report']['candidate_count']} cells) gets an expensive 1km wide-radius
verification pass — restricting the expensive step to candidates is what keeps it affordable.
''')

# Colors match the static export (data/processed/nairobi_combined_hotspot_report.png):
# 'narrow,saturated' is deliberately not red — the built-up layer itself renders in red, so a
# red marker over built-up terrain (the common case for this flag) would be invisible.
SOURCE_STYLE = {
    'narrow': {'color': '#FF6600', 'label': 'Narrow-edge candidate'},
    'saturated': {'color': '#9400D3', 'label': 'Saturated candidate'},
    'narrow,saturated': {'color': '#00CC00', 'label': 'Flagged by both methods'},
}

st.subheader('Interactive map')
m = folium.Map(location=[-1.29, 36.868], zoom_start=11, tiles='CartoDB positron', scrollWheelZoom=False)
for r in candidates:
    style = SOURCE_STYLE[r['source']]
    folium.CircleMarker(
        location=[r['lat'], r['lon']],
        radius=7,
        color=style['color'],
        weight=2,
        fill=True,
        fill_color=style['color'],
        fill_opacity=0.85,
        popup=folium.Popup(
            f"<b>{style['label']}</b><br>"
            f"Narrow (500m cell) diff: {r['diff_pp']:+.1f}pp<br>"
            f"Wide (1km radius) diff: {r['wide_diff_pp']:+.1f}pp",
            max_width=240,
        ),
    ).add_to(m)
st_folium(m, use_container_width=True, height=520, returned_objects=[])
st.caption('🟠 narrow-edge · 🟣 saturated · 🟢 flagged by both (e.g. Mathare). Click a marker for its numbers.')

st.subheader('Ranked candidates')
tab1, tab2 = st.tabs(['By narrow-edge diff', 'By wide-radius diff'])
df = pd.DataFrame(candidates)
display_cols = ['lon', 'lat', 'source', 'diff_pp', 'wide_diff_pp']
col_names = {'lon': 'Lon', 'lat': 'Lat', 'source': 'Source', 'diff_pp': 'Narrow diff (pp)', 'wide_diff_pp': 'Wide diff (pp)'}
with tab1:
    st.caption('Sharp local edges — this is what a grid-only scan would surface.')
    top = df.sort_values('diff_pp', ascending=False)[display_cols].head(20).rename(columns=col_names)
    st.dataframe(
        top.style.format({'Lon': '{:.4f}', 'Lat': '{:.4f}', 'Narrow diff (pp)': '{:+.1f}', 'Wide diff (pp)': '{:+.1f}'}),
        hide_index=True, use_container_width=True,
    )
with tab2:
    st.caption('Wider-context signal — this is what catches settlements like Kibera that a narrow scan misses.')
    top = df.sort_values('wide_diff_pp', ascending=False)[display_cols].head(20).rename(columns=col_names)
    st.dataframe(
        top.style.format({'Lon': '{:.4f}', 'Lat': '{:.4f}', 'Narrow diff (pp)': '{:+.1f}', 'Wide diff (pp)': '{:+.1f}'}),
        hide_index=True, use_container_width=True,
    )

st.info('''
**Why two tables, not one ranking:** narrow diffs run up to +56pp while wide diffs cap around
+20pp, so a single blended score buries every saturated candidate (Kibera included) under the
narrow-edge list. Reporting both separately is the actual finding of notebook 07 — not a UI
nicety, a documented limitation of collapsing the two signals into one number.
''')

with st.expander('Static export with legend'):
    st.image(image_path('nairobi_combined_hotspot_report.png'), use_container_width=True)

st.caption(
    'Method detail: notebooks/07_combined_hotspot_report.ipynb · '
    'full candidate table: data/processed/combined_riparian_hotspots.csv'
)
