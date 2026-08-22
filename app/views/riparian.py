import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import image_path, load_summary

st.title('🌿 Riparian Buffer Analysis')

summary = load_summary()
rivers = summary['rivers']
city = summary['city_wide']

st.markdown(f'''
Nairobi's river network ({rivers['reach_count']} reaches, {rivers['total_length_km']:.0f} km
total, HydroSHEDS Free-Flowing Rivers) compared against the 2024 built-up classification. Buffer
widths are swept (30/50/100m) rather than fixed to one number — an analytical choice, not a claim
about Kenya's legally tiered riparian reserve width under the Water Act / NEMA guidelines.
Nairobi National Park is excluded (protected land with no legal development would mechanically
drag down the comparison regardless of real encroachment elsewhere).
''')

st.subheader('City-wide: riparian buffer vs. rest of the city')
df = pd.DataFrame(city['buffer_sweep'])
df.columns = ['Buffer (m)', 'In-buffer built-up %', 'Rest-of-city %']
st.dataframe(df.style.format({'In-buffer built-up %': '{:.1f}%', 'Rest-of-city %': '{:.1f}%'}), hide_index=True, use_container_width=True)

st.info(f'''
**Surprising result:** city-wide, riparian buffers do **not** show elevated built-up fraction —
flat to slightly *below* the rest of the city ({city['builtup_pct_excl_park']:.1f}% built-up
city-wide, excl. park). That's the opposite of the "informal settlements crowd riverbanks"
narrative. But this aggregate hides real local hotspots — see below.
''')

st.subheader('Known informal settlements, checked by hand')
st.caption('Not discovered by the pipeline — chosen from documented literature, then verified. See the Systematic Grid Scan and Combined Hotspot Report pages for how this project later found hotspots without prior knowledge of where to look.')
hs = pd.DataFrame(summary['named_hotspot_cross_check'])
hs = hs.rename(columns={'name': 'Location', 'wide_diff_pp': 'Riverside vs. surrounding (pp)', 'narrow_diff_pp': 'Within-500m-cell diff (pp)'})
st.dataframe(
    hs[['Location', 'Riverside vs. surrounding (pp)', 'Within-500m-cell diff (pp)']]
    .style.format({'Riverside vs. surrounding (pp)': '{:+.1f}', 'Within-500m-cell diff (pp)': '{:+.1f}'}),
    hide_index=True, use_container_width=True,
)
st.caption('Mathare and Kibera show a real riverside effect at wider (1km) radius; Kibera nearly vanishes at the tighter 500m grain — see Systematic Grid Scan for why.')

st.image(
    image_path('nairobi_riparian_buffer_builtup.png'),
    caption='Built-up classification with 30m riparian buffer overlay (cyan)',
    use_container_width=True,
)

st.caption('Method detail: notebooks/05_riparian_buffer_analysis.ipynb')
