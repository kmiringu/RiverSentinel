import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import load_summary

st.title('🌊 RiverSentinel')
st.subheader('Find houses built too close to Nairobi\'s rivers — before you send a team to check.')

summary = load_summary()
kasarani = summary.get('buildings', {}).get('kasarani')

if kasarani:
    col1, col2, col3 = st.columns(3)
    col1.metric('Buildings flagged in Kasarani', f"{kasarani['encroaching_count']:,}")
    col2.metric("Pamoja Trust's own field count", f"~{kasarani['pamoja_trust_reported_count']:,}")
    col3.metric('Screening distance used', f"{kasarani['calibrated_distance_m']}m from a river")

st.markdown('''
### What this does

Pamoja Trust has walked the riverbanks of Kasarani by hand to find houses built too close to the
river. That kind of survey is slow and expensive to repeat, and it's hard to know where to look
next once one area is done.

RiverSentinel does the same job with satellite images and building data instead of a walking
survey: it finds every building in an area, measures how close each one is to a river, and hands
back a list of the ones worth checking in person — coordinates included, ready to hand to a field
team.

**It found 725 buildings within 18 meters of a river in Kasarani. Pamoja Trust's own survey found
about 700.** That's close enough to trust as a starting point, not close enough to skip the field
visit — every flagged building still needs someone to go look.

**→ Open "Encroaching Buildings" in the sidebar to see the list, the map, and download it.**
''')

with st.expander("How sure can I be about this?"):
    st.markdown('''
    Getting close to the right *total* isn't the same as flagging the exact *same* buildings
    Pamoja Trust found by hand — we don't have their building-by-building list to check against,
    only the total they reported. It's possible some of our 725 aren't real encroachments, and
    some real ones aren't on our list. Treat this as a strong first pass that narrows down where
    to look, not a replacement for someone actually walking out and checking.
    ''')

with st.expander("Where the data comes from"):
    st.markdown('''
    - **Building locations:** Google's Open Buildings project, which uses satellite imagery and
      machine learning to map individual building footprints across Africa.
    - **River locations:** a global river dataset (HydroSHEDS), matched against satellite imagery
      of Nairobi.
    - **The 18-meter screening distance:** not a legal boundary — we tested several distances and
      picked the one that landed closest to Pamoja Trust's own reported count in Kasarani.

    Full technical detail, every method tried and every dead end, lives under **Technical
    Methodology** in the sidebar and in this project's `RESEARCH_LOG.md`.
    ''')
