# 2. Approach and Methods — Planned vs. Built

The project has two logically separate tracks. Track A was built as planned. Track B was
**replanned mid-project and the README was never brought in line with that change** — this is
the single biggest gap between what the docs claim and what runs. That gap is the main thing
this doc exists to make explicit.

## Track A: city-wide trend detection (Sentinel-2 + Random Forest)

**What:** classify every 10m pixel in Nairobi as built-up or not, from free Sentinel-2 satellite
imagery, using a Random Forest trained against ESA WorldCover labels.

**Why this approach:** Sentinel-2 is free, revisits Nairobi every few days, and covers the whole
city — good for a *trend* signal (is built-up density near rivers changing, and where) even
though it can't resolve individual buildings (see [01-problem-statement.md](01-problem-statement.md)).

**Status: built as planned.** This is notebooks 01-07, described in detail in
[03-pipeline-walkthrough.md](03-pipeline-walkthrough.md). Held-out accuracy ~86%. Includes one
explicitly rejected result (2019→2024 change detection, notebook 04) reported honestly rather
than hidden — see that walkthrough.

## Track B: which specific buildings encroach

This is where the plan and the build diverge.

### What was planned (README + `off_grid.md`)

The README's "Solution" section states: *"the 50cm imagery drives YOLOb8-seg for accurate
one-time-or-periodic building counts."* `off_grid.md` (written 2026-08-25) works out what that
would actually require:

- 200-500 hand-collected 640×640px tiles of 50cm-resolution imagery, split across dry/wet season
- 3,000-5,000 individually-drawn building polygons for training
- An annotation tool (recommended: Roboflow, for its YOLOv8-seg export format and AI-assisted
  polygon tracing) and a validation workflow across annotators
- Training a YOLOv8 segmentation model on that hand-labeled dataset
- A tiling/deduplication strategy for buildings that straddle tile boundaries

**None of this was executed.** There is no 50cm imagery in this repo, no annotated dataset, no
Roboflow project, no trained YOLO weights, and no training notebook. `off_grid.md` is a sizing
and tooling *plan* — a "here's what it would take" document — not a record of work done. A
repo-wide search confirms "yolo" appears in exactly two files: the README's aspirational
sentence and this planning doc.

### What was actually built instead: Google Open Buildings

**Why the plan changed** (documented in `RESEARCH_LOG.md`, 2026-08-22 pivot entry): training a
custom segmentation model was evaluated and ruled out, not just skipped —

- A single Sentinel-2 pixel (10m) is already larger than most individual houses, so **there is
  no free source of the 50cm imagery the plan itself said was required** for Kenya.
- Even with imagery in hand, the annotation work `off_grid.md` scopes out (3,000-5,000 hand-drawn
  polygons) is real, multi-week labeling work, plus a GPU training pipeline — both out of scope
  for a capstone timeline.

**What replaced it:** Google's **Open Buildings** dataset
(`GOOGLE/Research/open-buildings/v3/polygons` in Earth Engine) — individual building footprint
polygons across Africa, already produced by a CNN Google trained and published. The project
reuses that trained model's *output* (footprint polygons + confidence scores) rather than
training its own detector. Each building's distance to the nearest river is then computed by
sampling the same `dist_to_river` raster Track A already built. This is notebook 08 — see the
walkthrough doc for what it actually measured.

**Practical difference this makes:** Open Buildings gives footprints and locations, not a
learned understanding of what a "shack" looks like in imagery the way a trained segmentation
model would. It can't be pointed at new, unmapped imagery the way a YOLO model could — it's a
fixed dataset lookup, not a detector. That's a real capability gap relative to what the README
promises, not just a naming difference.

## The takeaway

Read literally, the README describes a two-model system: Random Forest for trend, YOLOv8-Seg for
counts. What ships is: Random Forest for trend, **a pretrained third-party dataset lookup** for
counts. The second half works, is calibrated against a real (if unverified) reference number, and
is arguably a *better* engineering decision for a capstone timeline than the original plan — but
it is not YOLOv8-Seg, and the README should say so. See
[04-status-and-gaps.md](04-status-and-gaps.md) for the full reconciliation, including the other
claimed business deliverables that were never built either.
