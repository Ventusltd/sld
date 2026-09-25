# The two-channel drawing furnace

The established pattern is retained from
https://github.com/Ventusltd/worlds-/blob/b5f15716486c3ff509c56914fbee06f2e6aec2d8/src/furnace.py:
one fused CUDA implementation and a separately expressed CuPy reference run on
the same GPU. The related annihilation experiment deliberately compares strict
and inclusive thresholds. This implementation records touching boxes separately
from overlap; an equality case is not hidden as a failure.

## What this experiment actually asks

For every ordered pair of acquired component definitions with finite positive
declared width and height, place one at the origin and the second at every
half-unit offset in a 1024 by 1024 grid. Repeat for three distinct clearances:
0, 2 and 4 drawing units. These are graphic units, not metres or electrical
clearance requirements. Each component-pair/offset/clearance tuple is a unique
case. Repeated timing or warm-up runs are not counted as new cases.

The electron uses interval intersection in a CUDA kernel. The positron uses
centre distances and half-width sums through CuPy array operations. They must
agree whether declared rectangles are separated, touching or overlapping.
Nine hand-calculated threshold fixtures, a CPU sample and an injected mismatch
check provide additional checks. Both channels share declared input dimensions;
they cannot detect an upstream dimension that is itself wrong.

The output is bounded: one compact geometry-input photon and one evidence
photon, irrespective of billions of computed cases. Intermediate arrays remain
on the GPU in bounded batches. The receipt reports compile/setup and whole-run
time separately from each measured iteration. Existing accepted output is
invalidated before a new attempt; publication keeps the previous good release
until a complete new attempt passes all gates.

## What it does not establish

This is an exhaustive check of the defined rectangular layout domain. It does
not compare actual SVG outlines, labels or conductor routes, solve load flow,
validate protection, prove standards conformity, or approve an electrical design.
Graphical anchors are not inferred to be electrical terminals. Production symbol
approval still requires reviewed approved-project evidence dated after 2012.

## Running

Use an existing CUDA-capable Python environment with CuPy and NumPy:

```text
python scripts/fetch_sources.py
python scripts/build_catalogue.py
python scripts/furnace.py --out E:/sld-furnace/current
```

The initial fetch requires explicit `--accept-first-fetch`; subsequent fetches
must match the committed source lock. Use `--grid 16 --gaps 0` for a smoke test,
not a billion-case claim. The default produces three full distinct sweeps.
No copyrighted standards database or confidential project documents are inputs.
