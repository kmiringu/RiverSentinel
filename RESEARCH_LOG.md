# RiverSentinel — Research Log

Running record of the build: what was tried, what happened, and the reasoning behind each
decision — written as we go. This is not the README.

---

## 2026-08-13 — Repo scaffolding

Initialized the repo (`git init`, default branch renamed `master` → `main`). Adopted a hybrid
structure: `notebooks/` for exploration, `src/` for code that's graduated from "I think this
works" to "proven, reused" — mirroring how `jali_generator.py` worked for the earlier shelved
capstone idea. `data/` (raw + processed) is fully gitignored: geospatial files are large and
reproducible from the pipeline, not something to store in git history.

Python venv + `requirements.txt` (earthengine-api, geemap, geopandas, rasterio, shapely, folium,
scikit-learn, streamlit, jupyter, matplotlib) — installed clean after one retry (a plain network
timeout on a large wheel, not a GDAL/binary compatibility issue, which was the anticipated risk).
Versions deliberately left unpinned for now; freezing them is deferred until closer to
submission, once the dependency set has stopped changing.

Earth Engine authenticated and confirmed working end-to-end (a real round-trip API call, not just
"a token file exists"). Google Cloud Project ID: `solar-haven-349708` — required in every
`ee.Initialize()` call from here on.

---

## 2026-08-13 — Notebook 01: Nairobi imagery acquisition

**Objective:** prove the Earth Engine acquisition mechanics work end-to-end before building
anything analytical on top of unproven plumbing.

**Method:** Nairobi boundary from Earth Engine's built-in FAO GAUL administrative dataset
(`ADM0_NAME='Kenya'`, `ADM1_NAME='Nairobi'`) — no external file to source. Sentinel-2 Surface
Reflectance (Harmonized), filtered to June–September 2024 (dry season, chosen for lower expected
cloud cover) with a <20% per-scene cloud threshold, combined via median composite.

**Result:** exactly 1 matching boundary feature, centroid at lat -1.290 / lon 36.868 (correct).
11 scenes passed the filter. Composite visually confirmed as Nairobi — recognizable CBD, and
Nairobi National Park visible as a distinct dark wedge in the southeast.

**Limitation found:** visible straight-edge seams in the composite — not cloud artifacts, but
boundaries where different Sentinel-2 orbital footprints meet. Color tone blends smoothly across
them; only the geometric edges are visible.

**Decision:** leave the seams. They're cosmetic — the underlying reflectance values are still
valid — and don't block the classification work that depends on this composite. Revisit only if
they turn out to matter later.

---

## 2026-08-13 — Notebook 02: Built-up classification, baseline

**Objective:** classify built-up vs. non-built-up with a real, measured accuracy number instead
of a visual guess.

**Method:** NDBI (`(SWIR1-NIR)/(SWIR1+NIR)`, Sentinel-2 bands B11/B8), thresholded at the
textbook default of 0 — deliberately untuned, to measure how far a naive baseline gets. Validated
against ESA WorldCover 2021's built-up class (`ESA/WorldCover/v200`, value 50) as an independent
reference — not ground truth, but a real external check rather than an invented number.

**Prediction made before running:** agreement under 80%.

**Result:** 62.0% pixel agreement. NDBI classified 56.4% of Nairobi as built-up; WorldCover put
it at 31.9% — NDBI over-classifying by nearly 2×.

**Diagnosis:** Nairobi National Park (dry-season bare soil / dry grassland) was largely
misclassified as built-up. Dry vegetation and concrete both have low vegetation reflectance
relative to SWIR, so a single index can't tell them apart.

---

## 2026-08-13 — Notebook 02: NDVI-combined iteration

**Objective:** fix the bare-soil/dry-grass confusion without yet reaching for a trained model.

**Method:** added a second condition — NDBI > 0 **and** NDVI < 0.2 (`(NIR-Red)/(NIR+Red)`,
bands B8/B4) — to reject pixels with even moderate vegetation, another untuned textbook default.

**Result:** agreement rose to **81.7%** (from 62.0%). The park is now correctly mostly
non-built-up. But built-up fraction dropped to **17.8%** (WorldCover: 31.9%) — the error flipped
from over- to under-classification.

**Interpretation:** fixed the big spatial error (the park) but introduced a new, smaller one —
the NDVI cutoff is likely too strict in mixed or tree-covered suburban areas that are genuinely
built-up.

---

## 2026-08-14 — Notebook 02: NDVI threshold sweep

**Objective:** rather than guess a second NDVI cutoff, measure a range of values and let the data
pick the threshold.

**Method:** swept NDVI < {0.15, 0.20, 0.25, 0.30, 0.35, 0.40} at fixed NDBI > 0, measuring
agreement and built-up fraction at each.

**Result:**

| NDVI cutoff | Agreement | Built-up fraction |
|---|---|---|
| 0.15 | 78.9% | 13.4% |
| 0.20 | 81.7% | 17.8% |
| 0.25 | 83.5% | 22.0% |
| **0.30** | **83.6%** | 26.6% |
| 0.35 | 81.2% | 32.6% |
| 0.40 | 76.5% | 39.8% |

(WorldCover built-up fraction: 31.9%, for reference.)

**Winner: NDVI < 0.30 — 83.6% agreement**, a clear peak degrading on both sides.

**Interesting nuance:** NDVI < 0.35 matches WorldCover's built-up *area total* almost exactly
(32.6% vs 31.9%) but scores *lower* pixel agreement than 0.30 (81.2% vs 83.6%). Aggregate area
matching and pixel-level correctness are not the same thing — 0.35 gets the total right while
misclassifying different pixels than WorldCover, with errors roughly canceling in the aggregate.
This is the concrete justification for using pixel agreement rather than area-total matching as
the evaluation metric: a classifier can look right in aggregate while being wrong in detail.

**Final baseline classifier: NDBI > 0 AND NDVI < 0.30, 83.6% agreement with WorldCover.**

**Open question for next session:** is 83.6% good enough to build the change-detection step on
top of, or is it worth trying the Random Forest classifier option from the original proposal to
push further? No decision made yet.

**Status:** written and executed, not yet committed to git (commits are done by hand, on
purpose — see below).

---

## 2026-08-15 — Notebook 03: Random Forest classification

**Objective:** resolve the open question from notebook 02 — does a trained classifier beat the
83.6% tuned threshold baseline, or does the simple approach hold up?

**Method:** `ee.Classifier.smileRandomForest` (100 trees, untuned, Earth Engine server-side —
consistent with the rest of the pipeline, no local array export needed). Features: the six raw
Sentinel-2 bands (B2, B3, B4, B8, B11, B12) plus NDVI and NDBI as engineered features, carrying
forward the domain knowledge from notebook 02 rather than discarding it. Labels: ESA WorldCover
built-up class, same reference as before — but now used as training data, not just a validation
check.

**Methodological guard:** training a classifier directly on WorldCover-derived labels and then
scoring it against WorldCover is close to circular if evaluated on the same pixels. To keep the
comparison against the baseline fair, labeled points were stratified-sampled (1500 points,
balanced across built-up/non-built-up) and split 70/30 into train/test *before* training. The RF
is only scored on the held-out 30% it never saw.

**Result:**

| Method | Metric | Value |
|---|---|---|
| Threshold baseline | full-image agreement vs. WorldCover | 83.6% |
| Random Forest | held-out point accuracy | **86.2%** |
| Random Forest | full-image agreement vs. WorldCover | 86.8% |

Confusion matrix on held-out points (rows=actual, cols=predicted, [not-built-up, built-up]):
`[[375, 74], [49, 392]]` — reasonably balanced error, unlike the threshold sweep's asymmetric
over/under-classification.

**Feature importance:** B11 (SWIR1) and B12 (SWIR2) ranked highest, NDBI close behind — the model
converged on the same physical signal NDBI was built from, rather than finding something
unrelated. The gain over the baseline looks like better calibration around the hard threshold
cutoffs, not a different underlying signal.

**Caveat:** RF built-up fraction is 38.0% vs. WorldCover's 31.9% — still over-classifying, less
than raw NDBI (56.4%) but more than the tuned threshold baseline (26.6%). Better pixel-level
accuracy, worse aggregate area calibration than the threshold approach — same
accuracy-vs-area-total distinction flagged in notebook 02.

**Decision: adopt the Random Forest classifier** (86.2% held-out accuracy) as the built-up layer
going forward, superseding the threshold baseline. It wins on the metric that matters (held-out
accuracy) with more balanced errors, at the cost of a small amount of aggregate-area calibration.

**Also fixed:** `ee.Classifier.smileRandomForest` takes `numberOfTrees=`, not `numTrees=` — the
Python API param name in the currently installed `earthengine-api` differs from what appears in
some older EE documentation/examples.

**Status:** written and executed, not yet committed to git.

---

## 2026-08-16/17 — Notebook 04: Change detection, and a real radiometric bug

**Objective:** apply the RF classifier to an earlier composite (2019 dry season, 8 scenes — 2017's
equivalent window only has 3, too sparse to trust) and measure built-up growth 2019→2024, the
first half of the project's stated goal.

**Approach:** train once on 2024 (the only year WorldCover labels are contemporaneous with),
apply the same fixed classifier to both composites — the methodologically correct choice for
change detection (a moving decision boundary would make "change" ambiguous between real change
and classifier drift).

**First result failed its own sanity check.** Built into the notebook from the start: "lost
built-up" (built-up in 2019, not in 2024) should be near-zero in a growing city — a large value
would mean the classifier is unstable across years, not that Nairobi de-urbanized. First run:
**32.1% lost built-up.** Far too large to be noise.

**Diagnosis, in two layers:**

1. Per-band means differed hugely across the whole city between composites (e.g. B4: 1770 in
   2019 vs. 952 in 2024) — a systematic brightness shift, not a land-cover signal. Not the known
   Sentinel-2 baseline-offset bug (already handled by `_HARMONIZED`) — wrong direction/magnitude
   for that. Applying linear (mean/stdDev) band normalization, 2019→2024, brought "lost built-up"
   down to ~16% — real progress, not a fix.
2. Checking band statistics *inside Nairobi National Park* (large, protected, presumed
   near-unchanged) explained the rest: 2019's park-interior stdDev was **5–10x higher** than
   2024's in visible bands (B2: 1063 vs. 99) — far too much internal variance for a spectrally
   uniform natural area. Root cause: `acquisition.py` only ever filtered by whole-scene
   `CLOUDY_PIXEL_PERCENTAGE`, no per-pixel cloud/shadow mask. Fine with 11 clean scenes going into
   a 2024 median; not fine with only 8 scenes in 2019, where a median has fewer alternatives to
   outvote a contaminated pixel.

**Fix applied at the source, not papered over:** `acquisition.py`'s `get_sentinel2_composite` now
masks cloud/shadow/cirrus per-pixel via the Sentinel-2 SCL band before compositing — a real
correctness fix to the shared, reused module. Notebook 03 was re-run against it as a regression
check: 86.2%→85.9% held-out accuracy, negligible drift, confirming the bug mattered for the
sparse year and was invisible in the well-covered one.

**Masking alone still wasn't enough** (~21% lost built-up remained) — combining masking with the
mean/stdDev band normalization got it down to **11.0%**, the best result found. Graduated into
`src/classification.py` as `normalize_to_reference()` since it's now used twice (this notebook,
future cross-date work).

**Final numbers (masked + normalized):**

| Metric | Value |
|---|---|
| Built-up fraction, 2019 (normalized) | 40.2% |
| Built-up fraction, 2024 | 37.2% |
| Net change | -3.0 percentage points |
| New built-up | 8.2% of Nairobi |
| Lost built-up (noise check) | 11.0% of Nairobi |

**Honest conclusion — this is a methodological finding, not a growth measurement.** Visually, the
new-built-up layer is diffuse salt-and-pepper noise spread evenly across the city, not
concentrated growth at the urban fringe (what real 5-year growth should look like spatially). The
-3.0pp net "shrinkage" is implausible for a growing city and sits inside the residual noise band.
**Decision: do not report the pixel-level change map or the net percentage as a real finding.**
Naive independent per-date classification with an absolute-reflectance RF is not yet reliable
enough for pixel-level change detection here, even after masking and normalization.

**Also tried and explicitly rejected:** pseudo-invariant-feature (PIF) normalization using
Nairobi National Park's interior as the sole calibration region — overcorrected badly (2019
built-up fraction collapsed to an implausible 5.3%) because the park's own statistics were still
cloud-contaminated in the pre-masking test. Not re-tested post-fix; noted as the most promising
next step (a more careful multi-region PIF set, or proper atmospheric correction) if pixel-level
change detection is needed later.

**Status:** notebook 04 written and executed with an honest negative/mixed result; notebook 03
re-executed and re-committed with updated numbers reflecting the acquisition.py fix; not yet
committed to git.

---

