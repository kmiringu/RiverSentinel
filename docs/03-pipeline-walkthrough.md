# 3. Pipeline Walkthrough — What Each Piece Does and Produces

This is a plain-language map of the eight notebooks and the app that reads their output. Full
narrative detail, including every dead end, lives in `RESEARCH_LOG.md` — that file is the
authoritative record; this doc is a distilled reference, not a replacement.

## Notebooks

| # | Notebook | Question asked | Result | Status |
|---|---|---|---|---|
| 01 | Nairobi imagery acquisition | Does the Earth Engine pull actually work end-to-end? | Sentinel-2 median composite, June-Sept 2024, 11 scenes, visually confirmed | Working plumbing |
| 02 | Built-up classification, baseline | Can a simple spectral index (NDBI, then NDBI+NDVI) classify built-up land? | Tuned threshold (NDBI>0, NDVI<0.30): 83.6% agreement with ESA WorldCover | Superseded by 03 |
| 03 | Random Forest classification | Does a trained classifier beat the tuned threshold? | Yes — 86.2% held-out accuracy vs. 83.6% baseline | **Adopted** — used by every later notebook |
| 04 | 2019→2024 change detection | Where has built-up land grown? | A real radiometric bug found and fixed (per-pixel cloud masking), but result still implausible (-3.0pp "shrinkage" in a growing city) | **Rejected, reported honestly as a negative result** — not used downstream |
| 05 | Riparian buffer analysis | Is built-up density higher right next to rivers? | City-wide: flat/no signal. But Mathare (+9.6pp) and Kibera (+8.5pp) show a real local effect when checked individually; Mukuru shows none because it's saturated built-up everywhere | Confirmed: encroachment is real but spatially concentrated, not a uniform city-wide pattern |
| 06 | Systematic hotspot scan | Can hotspots be found without already knowing where to look (05 used documented settlements)? | 500m city-wide grid scan; found new candidates *and* a real blind spot — Kibera's effect vanishes at fine grain because it's saturated on both sides | Confirmed a genuine methodological trade-off (narrow-edge vs. saturation), not a bug |
| 07 | Combined hotspot report | Can 05's and 06's signals run together as one output? | 49 merged candidates (narrow-edge + saturated), verified against Mathare/Kibera/Mukuru | Adopted as the pixel-level headline output |
| 08 | Building-level encroachment (Open Buildings) | Which *specific buildings* are in the riparian buffer? | Kasarani: 1,227 buildings within 30m (uncalibrated); calibrated to Pamoja Trust's reported ~700 → 18m buffer gives 725 (closest match found) | **The project's current deliverable** — see [02-approach-and-methods.md](02-approach-and-methods.md) for what this is (and isn't) |

**A note on what "accuracy" means here:** every accuracy/agreement number above is measured
against ESA WorldCover, an independent satellite-derived reference layer — not hand-labeled
ground truth. It's a real external check, but not the same strength of evidence as verified field
data. The Pamoja Trust ~700 figure used to calibrate notebook 08 is the only number in this
project sourced from an actual field survey, and even that is a reported total, not a verified
building-by-building list (see [01-problem-statement.md](01-problem-statement.md)).

## Reusable code (`src/`)

Per this project's own rule, code only moves out of a notebook and into `src/` once it's reused
in more than one place — nothing here was extracted speculatively:

- `src/acquisition.py` — Sentinel-2 composite fetch + per-pixel cloud/shadow masking (the fix
  from notebook 04's radiometric bug)
- `src/classification.py` — Random Forest feature building, training, and cross-date band
  normalization
- `src/riparian.py` — river distance raster, wide-radius built-up comparison, and paginated
  Earth Engine feature fetch (needed once Kasarani's building set passed EE's ~5000-row
  `getInfo()` cap)

## The Streamlit app (`app/`)

Reads precomputed exports from `data/processed/` (JSON summaries + CSVs); only one page
(`live_check.py`) makes a live Earth Engine call.

| Page | Nav group | What it shows |
|---|---|---|
| Overview (`home.py`) | RiverSentinel | Headline Kasarani numbers (725 flagged vs. ~700 Pamoja Trust), plain-language framing, links to the building list |
| Encroaching Buildings (`buildings.py`) | RiverSentinel | Interactive map + downloadable CSV of flagged buildings, calibration story |
| Draw Your Own Area (`custom_area.py`) | RiverSentinel | Live Earth Engine query for a user-drawn rectangle/circle, capped at 30km², reusing notebook 08's method |
| Built-up Classification (`classification.py`) | Technical Methodology | Notebook 03's Random Forest, summarized |
| Riparian Buffer Analysis (`riparian.py`) | Technical Methodology | Notebook 05's city-wide + hotspot comparison |
| Systematic Grid Scan (`grid_scan.py`) | Technical Methodology | Notebook 06's 500m grid scan |
| Combined Hotspot Report (`combined.py`) | Technical Methodology | Notebook 07's merged candidate list |
| Live Point Check (`live_check.py`) | Technical Methodology | On-demand Earth Engine classification for an arbitrary point |

Data behind every page except Live Point Check and Draw Your Own Area comes from
`data/processed/pipeline_summary.json` and a handful of CSVs — nothing in the main app flow
trains a model or queries Earth Engine at page-load time.

## What "expected output" means for this project

Concretely, running this pipeline end-to-end produces:

1. A **trend picture** — is riverside built-up density rising, and where (notebooks 03-07,
   `data/processed/*.png`, `combined_riparian_hotspots.csv`).
2. A **building-level candidate list** — specific lon/lat/confidence/distance-to-river rows a
   field team could actually drive to (`kasarani_encroaching_buildings.csv`,
   `other_hotspots_encroaching_buildings.csv`).
3. An **interactive app** a non-technical stakeholder can open, read the headline number, and
   download the candidate list from, without needing to open a notebook.

It does **not** currently produce the three "business deliverables" named in the README (risk
tiers, population/infrastructure exposure, a growth-velocity timeline) — see
[04-status-and-gaps.md](04-status-and-gaps.md).
