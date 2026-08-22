import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import image_path, load_summary

st.title('🏙️ 2024 Built-up Classification')

summary = load_summary()
c = summary['classification']

st.markdown(f'''
Random Forest classifier (100 trees) trained on Sentinel-2 surface reflectance bands plus
NDVI/NDBI, using ESA WorldCover's built-up class as the training and validation reference. Built
from **{c['scene_count']} cloud-filtered scenes** (June–September 2024 dry-season composite,
per-pixel cloud/shadow masked via the Sentinel-2 SCL band — a real bug fix in
`src/acquisition.py`, not the default whole-scene filter). Every later page's built-up map comes
from this classification.
''')

st.metric('Held-out test accuracy', f"{c['held_out_accuracy_pct']:.1f}%")

st.image(
    image_path('nairobi_builtup_random_forest.png'),
    caption='2024 built-up classification (red = built-up)',
    use_container_width=True,
)

st.caption(
    'Method detail: notebooks/03_random_forest_classification.ipynb · '
    'features: B2, B3, B4, B8, B11, B12, NDVI, NDBI'
)
