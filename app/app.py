import streamlit as st

st.set_page_config(page_title='RiverSentinel', page_icon='🌊', layout='wide')

home = st.Page('views/home.py', title='Home', icon='🌊', default=True)
classification = st.Page('views/classification.py', title='Built-up Classification', icon='🏙️')
riparian = st.Page('views/riparian.py', title='Riparian Buffer Analysis', icon='🌿')
grid_scan = st.Page('views/grid_scan.py', title='Systematic Grid Scan', icon='🔎')
combined = st.Page('views/combined.py', title='Combined Hotspot Report', icon='🎯')
live_check = st.Page('views/live_check.py', title='Live Point Check', icon='📍')

pg = st.navigation([home, classification, riparian, grid_scan, combined, live_check])
pg.run()
