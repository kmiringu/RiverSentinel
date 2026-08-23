import streamlit as st

st.set_page_config(page_title='RiverSentinel', page_icon='🌊', layout='wide')

home = st.Page('views/home.py', title='Overview', icon='🌊', default=True)
buildings = st.Page('views/buildings.py', title='Encroaching Buildings', icon='🏠')
custom_area = st.Page('views/custom_area.py', title='Draw Your Own Area', icon='📐')
classification = st.Page('views/classification.py', title='Built-up Classification', icon='🏙️')
riparian = st.Page('views/riparian.py', title='Riparian Buffer Analysis', icon='🌿')
grid_scan = st.Page('views/grid_scan.py', title='Systematic Grid Scan', icon='🔎')
combined = st.Page('views/combined.py', title='Combined Hotspot Report', icon='🎯')
live_check = st.Page('views/live_check.py', title='Live Point Check', icon='📍')

pg = st.navigation({
    'RiverSentinel': [home, buildings, custom_area],
    'Technical Methodology (how it works under the hood)': [classification, riparian, grid_scan, combined, live_check],
})
pg.run()
