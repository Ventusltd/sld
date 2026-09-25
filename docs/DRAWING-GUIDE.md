# Learning to read and assemble an SLD

This library is an educational research collection with a UK / IEC preference. No component is approved for production. Open licensing, plausible geometry and successful software tests do not establish engineering conformity.

## SLD and block diagram

A single-line diagram represents electrical equipment and connectivity while simplifying multiple conductors into a line. Its scope and conventions must be stated. A block diagram represents functions or information flow; a line between its boxes does not establish electrical connectivity.

The drawing bench makes an **illustrative sketch**. Its dashed links join graphical centres, not electrical terminals. Overlapping lines are crossings without a connection. To express a junction in a sketch, add a separate junction component and connect the intended parts explicitly. Exported JSON records only these illustrative links; it is not a power-system model or a certified interchange format.

## Electrical terminals and graphical anchors

An equipment terminal is an electrical connection point. A connectivity node identifies an electrically common junction. A graphical anchor is a renderer's location for drawing a line: it can be one of several alternatives for a single terminal.

For example, the imported disconnector has one graphical anchor although a switch connects two electrical terminals. The generator has four graphical anchors for drawing direction choices. Do not infer terminal count or connection meaning from these anchor arrays.

Transformer assets can be individual winding fragments. The preview builder overlays the required upstream subcomponents and preserves source geometry. The raw library also retains the upstream orientation/transformation metadata for other drawing tools. A tool implementing rotations or flips must transform its selected anchors consistently and separately map electrical terminals to them.

## Source, licence and engineering evidence

PowSyBl's ConvergenceLibrary provides the actual source SVG files and component metadata under MPL-2.0. The pinned source revision, file URLs and SHA-256 hashes are recorded in `data/library.json`; exact source bytes remain in `data/upstream/powsybl/`. Generated preview files are derivatives, with attribution retained. Preserve the licence and applicable notices, and meet its source-availability requirements when distributing covered files or modifications.

Several component definitions are renderer primitives or values, rather than standalone SVG symbols. Their previews are marked as illustrative. An upstream name is not an independently verified description of a British-standard symbol. A generic ground graphic must not automatically become protective earth. A generic switch must not silently replace a circuit breaker or disconnector.

Standards documents and approved project drawings are evidence sources; their content is not automatically redistributable because an implementation is open source. Record reference identifiers and permitted evidence rather than copying restricted drawings into this public library.

## Unknown ratings stay unknown

The bench assigns no voltage, current, fault rating, phase information, transformer ratio, earthing arrangement or protection setting. Never derive these from symbol size, colour, position or an attractive rendering. Network parameters require their own sources, units and review. No load-flow or protection study is performed here.

## Review before production

1. Identify the intended equipment function and applicable UK / IEC convention.
2. Verify source provenance, asset licence and all required subcomponents/styles.
3. Map electrical terminals explicitly to the selected graphical anchors and test every supported orientation/state.
4. Match each part to an approved real-project drawing issued **after 2012**. Record drawing ID, revision, date, sheet, matched location, permitted evidence reference and reviewer.
5. Record engineering review and standards evidence separately from software checks. Missing or conflicting evidence keeps the part disabled.
6. Enable production only after all required checks are approved. A GPU similarity score, matching models or a passing browser test cannot substitute for approval.

## Reuse and draft files

Other drawing tools can consume [the component catalogue](../data/library.json). This contains upstream size, subcomponent, anchor and transformation data as well as source/status metadata. The browser's exported draft is a separate, deliberately small format: component instances with positions and illustrative links. It rejects unknown component IDs, duplicate IDs, invalid coordinates and invalid links, and discards unexpected fields. JSON is rendered as text and never executed as HTML.

Use the on-screen movement buttons on touch devices, or arrow keys after selecting a part. Delete removes that part and its links. JSON export preserves an editable sketch. SVG export packages preview images into a standalone drawing labelled educational; neither export is an engineering approval.
