import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import load_summary

st.title('🌊 RiverSentinel')
st.caption('Nairobi built-up area change detection & riparian encroachment monitor — Moringa School Capstone')

summary = load_summary()

col1, col2, col3 = st.columns(3)
col1.metric('2024 classification accuracy', f"{summary['classification']['held_out_accuracy_pct']:.1f}%")
col2.metric('City-wide built-up (excl. park)', f"{summary['city_wide']['builtup_pct_excl_park']:.1f}%")
col3.metric('Flagged riverside hotspots', summary['combined_report']['candidate_count'])

st.markdown('''
### What this project does
Classifies built-up land in Nairobi from Sentinel-2 imagery (Random Forest, validated against
ESA WorldCover) and asks where that built-up land currently sits relative to the river network —
riparian buffer encroachment, the second half of the project's stated goal.

Use the sidebar to walk through each stage of the pipeline:

- **Built-up Classification** — the 2024 Random Forest model behind every later page.
- **Riparian Buffer Analysis** — city-wide riverside vs. rest-of-city comparison, plus known
  informal-settlement hotspots checked by hand.
- **Systematic Grid Scan** — a 500m-grid scan that finds hotspots with no prior knowledge of
  where to look, and its own documented blind spot.
- **Combined Hotspot Report** — the two methods merged into one ranked, interactive candidate map.
- **Live Point Check** — click anywhere on a live map to run a real Earth Engine query at that
  point, on demand.
''')

st.warning('''
**What we tried and rejected:** an earlier 2019→2024 change-detection pass (comparing independent
per-date classifications) produced only diffuse noise, not a real growth signal, even after
fixing a real cloud-masking bug and adding band normalization. It is **not** reported as a
finding anywhere in this app — see `RESEARCH_LOG.md`, "Notebook 04", for the full write-up of
what was tried and why it was rejected.
''')

st.caption('Full build narrative, every decision and dead end: see `RESEARCH_LOG.md` in the repo.')
