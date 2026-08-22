import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import load_summary

st.title('🔎 Systematic Riparian Hotspot Scan')

summary = load_summary()
gs = summary['grid_scan']

st.markdown(f'''
The known hotspots on the Riparian Buffer Analysis page were chosen from documented literature,
not discovered by the pipeline. This scan removes that dependency: the city is split into a
{gs['grid_size_m']}m grid ({gs['total_cells']} cells, UTM 37S), and each cell's riverside
(within 30m of a river) built-up fraction is compared against the rest of that same cell.
{gs['cells_compared']} of {gs['total_cells']} cells had enough pixels on both sides
(minimum {gs['min_pixels']} px/side, ~2000m²) to trust the comparison.
''')

st.subheader('Top 15 candidates by within-cell riverside contrast')
df = pd.DataFrame(gs['top15_narrow_edge'])
df = df[['lon', 'lat', 'riverside_pct', 'rest_pct', 'diff_pp']]
df.columns = ['Lon', 'Lat', 'Riverside %', 'Rest-of-cell %', 'Diff (pp)']
st.dataframe(
    df.style.format({'Lon': '{:.4f}', 'Lat': '{:.4f}', 'Riverside %': '{:.1f}', 'Rest-of-cell %': '{:.1f}', 'Diff (pp)': '{:+.1f}'}),
    hide_index=True, use_container_width=True,
)
st.caption('Reported as coordinates, not asserted as named settlements — no ground-truthing or reverse-geocoding was done.')

st.warning('''
**Known blind spot:** this method structurally misses settlements uniformly dense on both sides
of the riverside line. Kibera scores only **+0.7pp** here — nearly invisible — despite showing a
real +8.5pp effect at wider (1km) radius (Riparian Buffer Analysis page). A grid-only ranking
would silently drop Kibera as a non-hotspot. See the Combined Hotspot Report page for how this
gets caught instead of missed.
''')

st.caption('Method detail: notebooks/06_systematic_hotspot_scan.ipynb')
