# sld
An open electrical drawing library, educational drawing bench and source catalogue.
UK/IEC conventions and metric units are the intended defaults. Components are
research candidates, not certified or approved production drawings.

Website: https://ventusltd.github.io/sld/

## What is assembled

- 35 PowSyBl component definitions, 37 original SVGs, assembly metadata and styles
  with the upstream MPL-2.0 licence. Four renderer primitives are labelled separately.
- A 2023 Newcastle/Keele OpenDSS demonstrator model under CC BY 4.0.
- A 2014 UK government illustrative SLD under OGL v3.0.
- Reference links for other university and industry sources whose reuse rights
  have not been established. These are not silently copied into the library.

The top search finds symbols and sources. Click components to assemble an
educational draft, move them, add illustrative links, and export/import JSON or
export SVG. Graphical anchors are distinct from electrical terminals. Centre
links on the teaching canvas do not constitute a validated electrical netlist.

## Change the catalogue

Edit `sources.yaml` (JSON-compatible YAML), preserving immutable revisions and
explicit licence evidence. Fetching is bounded and checks every source against
`data/source-lock.json`. New sources require a reviewed lock update. Retrieved
models are stored as text, never executed by the fetcher.

```text
python scripts/fetch_sources.py --check-offline
python scripts/build_catalogue.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/verify_furnace.py
python scripts/build_site.py --out dist
```

The machine-readable entry point is `data/library.json`. Original assets and
their licence records are under `data/upstream/`. See [the drawing guide](docs/DRAWING-GUIDE.md),
[the furnace method](docs/FURNACE.md) and [autonomous publication](docs/AUTOMATION.md).

## Two photons

The local RTX 5070 Ti evaluated 3,636,461,568 distinct declared-bounding-box
placement cases using fused CUDA and a separate CuPy expression. Zero channel
disagreements; 2.44 seconds across the three measured sweeps, 2.85 seconds for the
whole initial run. The compact input and evidence photons are in `data/furnace/`.
They bind exact source and script hashes and distinguish overlap from contact.
This is geometric enumeration, not load-flow, protection or standards approval.
Changing the inputs requires fresh evidence before the website can publish.

Hosted Chromium checks validate the actual web artifact. The local refresh
controller can fetch, rerun stale furnace evidence and push updated outputs;
Pages publishes only after the complete gate passes. No local GPU runner accepts
untrusted pull-request code. A failed candidate preserves the last good website.

## Licence

Open to all. The code is under the Apache License 2.0 (see LICENSE). Original text, tables and ledgers produced by this repository are under CC BY 4.0: use them, and say where they came from. Material belonging to others keeps its own licence, named beside it; standards are cited by clause and value and never reproduced.
