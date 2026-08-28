# 1. Problem Statement

Plain-language restatement of what RiverSentinel is for, and a check on which parts of that
story are backed by something in this repo versus asserted without a source.

## The problem, in one paragraph

Nairobi's Rivers Commission has declared a Special Planning Area with a 30-to-60-meter riparian
buffer along rivers — building inside that buffer is not supposed to happen. Enforcing it means
knowing which specific buildings are inside it, across hundreds of kilometers of riverbank.
Agencies don't have the field staff to walk all of that by hand. **Pamoja Trust**, an NGO, has
done exactly that kind of manual walk-the-riverbank survey for one area — **Kasarani** — and
found it slow and hard to repeat or extend to the rest of the city. RiverSentinel exists to
answer the same question — *which buildings are encroaching?* — from satellite and building-
footprint data instead of a walking survey, so a field team knows where to go before they go.

## What's independently verified vs. what's asserted

The README's "Market Problem" section makes two quantitative claims. It's worth being clear
about which one this project actually checked and which one it didn't:

| Claim | Source | Status |
|---|---|---|
| Pamoja Trust's manual survey found ~700 encroaching buildings in Kasarani | Reported to the project as context | **Not independently verified.** Notebook 08 says this explicitly: *"Pamoja Trust's ~700 figure is a reported number provided as project context, not independently [verified]."* We don't have their building-by-building list, only their total. |
| A government blob-count model flags only 118 structures vs. Pamoja Trust's 700 | README market-problem framing | **No source anywhere in this repo.** No notebook computes it, no CSV contains it, and nothing here reproduces or cites where "118" comes from. It reads as an illustrative number for the pitch, not a measured result. |

Neither of these is a criticism of the underlying problem — the buffer-enforcement gap is real
and well-documented (Nairobi Rivers Commission SPA, Water Act / NEMA riparian reserve rules).
The point is narrower: this project's own evidence for "here's how bad the undercount problem
is" starts and ends with the ~700 Kasarani figure, itself explicitly caveated. The "118" figure
should be treated as an unverified anecdote in a pitch, not a project finding, until a source is
attached to it.

## Why resolution matters (the actual technical constraint)

The real, repo-backed version of the "blob effect" argument is simpler than the README's framing
and doesn't need the 118 number to make its point: Sentinel-2 imagery (used throughout notebooks
01-07) has **10-meter pixels**. A single informal-settlement house is routinely smaller than one
pixel. That means:

- Pixel-level classification (what notebooks 01-07 do) can only ever answer "what fraction of
  this area is built-up" — a density statistic.
- It **cannot** resolve or count individual buildings, no matter how well-tuned the classifier
  is. This isn't a model-quality problem; it's a physical resolution limit of the input imagery.
- Answering "which specific buildings encroach" requires object-level data at a much finer
  resolution than Sentinel-2 provides — sub-meter imagery, or someone else's building-footprint
  extraction already done for you.

That constraint is the actual reason the project needed a second component beyond the Sentinel-2
Random Forest pipeline — see [02-approach-and-methods.md](02-approach-and-methods.md) for what
was planned for that second component and what was actually built.
