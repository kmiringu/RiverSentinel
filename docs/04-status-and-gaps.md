# 4. Status and Gaps — What's Actually Done

Purpose of this doc: give a straight answer to "how close to done is this, really," by checking
every concrete claim in `README.md` against what actually exists in the code, notebooks, and
data — not against what a previous write-up said. Verified by grepping the repo and reading the
actual notebooks/src/app files as of 2026-08-28.

## Built, working, and verified against something real

- **Sentinel-2 acquisition + cloud/shadow masking** (`src/acquisition.py`) — notebooks 01, 04.
- **Random Forest built-up classification**, 86.2% held-out accuracy vs. ESA WorldCover
  (`src/classification.py`) — notebook 03, used by every downstream notebook.
- **Riparian buffer analysis at city and hotspot scale** — notebooks 05-07, culminating in a
  49-candidate combined hotspot list (`data/processed/combined_riparian_hotspots.csv`).
- **Building-level encroachment via Google Open Buildings**, calibrated to an 18m buffer against
  Pamoja Trust's reported Kasarani count (725 found vs. ~700 reported) — notebook 08.
- **A working Streamlit app** with 8 pages, reading precomputed exports, including one live
  Earth Engine page and one draw-your-own-area page.

## Built, but with an explicit caveat worth remembering

- **2019→2024 change detection (notebook 04)** — a real bug was found and fixed, but the final
  result is still reported as unreliable and explicitly *not* used anywhere downstream. This is
  intentional, documented honesty (per this project's own norm — see `RESEARCH_LOG.md`), not an
  unfinished task. Nothing to "complete" here; it's a closed, negative result.
- **The ~700 Pamoja Trust figure** underlying all of notebook 08's calibration is a reported
  number, not independently verified (notebook 08 says so itself). Every "725 vs. ~700" headline
  in the app inherits that caveat.
- **City-wide building counts** don't exist — only Kasarani (full) and the top-15 pixel-hotspots
  (partial, 86 buildings) have been screened. A true city-wide count needs Earth Engine's
  asynchronous `ee.batch.Export.table` path; the current notebooks only use the synchronous
  `getInfo()` pattern, which times out at that scale. Documented as future work in
  `RESEARCH_LOG.md`, not silently dropped.

## Claimed in `README.md`, not built at all

This is the list the user should treat as the real backlog, not the polish list.

| README claim | What actually exists | Gap |
|---|---|---|
| "50cm imagery drives YOLOv8-seg for accurate ... building counts" | Zero lines of YOLO code, no 50cm imagery, no annotated dataset, no trained model anywhere in the repo. `off_grid.md` is a sizing/tooling *plan*, never executed. | **Full gap.** The building-count deliverable is real but comes from Google Open Buildings (a different, pretrained approach), not YOLOv8-Seg. See [02-approach-and-methods.md](02-approach-and-methods.md). |
| "Prioritised Triage Action Queue: High/Med/Low Risk (CSV)" | CSVs exist (`kasarani_encroaching_buildings.csv` etc.) with `lon, lat, confidence, area_m2, distance_to_river_m`. **No risk tier column, no High/Med/Low bucketing anywhere** — checked `app/views/buildings.py` and notebook 08 directly. | **Full gap.** Would need a risk-scoring rule (e.g. binned on distance + confidence) added to notebook 08's export. |
| "Human & Logistical Exposure Dashboard" (population estimation, infrastructure-size flags) | No population multiplier, no density assumptions, no "unusually large structure" flag in any notebook, `src/`, or app page. | **Full gap.** Not started. |
| "Spatiotemporal Drift Velocity Log" (timeline, rapid-growth hotspots) | Notebook 04 (the only change-over-time work) was explicitly rejected as unreliable. No timeline or velocity metric exists in any later notebook. | **Full gap**, and arguably blocked — see below. |

## Why some of these aren't quick add-ons

The "Drift Velocity Log" deliverable isn't just unbuilt, it's currently **not achievable with
what this pipeline has proven so far**: the only multi-date comparison attempted (notebook 04)
was rejected as too noisy to trust. Building a velocity/timeline feature honestly would mean
either re-solving notebook 04's radiometric problem (the PIF/atmospheric-correction path it
flagged as future work) or finding a different data source for change-over-time — not just
wiring up a chart on top of existing output.

The other three (risk tiers, population/infrastructure exposure) are more tractable — they're
mostly scoring/labeling logic layered on data the pipeline already produces (distance, confidence,
footprint area) rather than new modeling work.

## Bottom line

The project's actual technical achievement — Sentinel-2 trend detection handed off to a
calibrated, pretrained-footprint building-level candidate list, wrapped in a usable app — is
real, methodologically careful, and honestly documented in `RESEARCH_LOG.md`. But the README's
"business case" framing (written 2026-08-24, after the Open Buildings pivot had already happened
on 2026-08-22) describes a different, more ambitious system than what got built: a custom-trained
segmentation model and three specific business-intelligence outputs, none of which exist yet.
Treat the README as a pitch/vision document until it's rewritten to match `RESEARCH_LOG.md`'s
account of what actually shipped — they currently disagree with each other on what this project
is.
