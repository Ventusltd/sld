# Reusing the Ventus pandapower fork

GitHub inspection on 25 September 2026 confirms [Ventusltd/pandapower](https://github.com/Ventusltd/pandapower) is a fork of [e2nIEE/pandapower](https://github.com/e2nIEE/pandapower). Its default branch is **develop**; the inspected head is [`109416d25abb77d75bd3622d7492e1db57ae678e`](https://github.com/Ventusltd/pandapower/commit/109416d25abb77d75bd3622d7492e1db57ae678e), committed 25 April 2026 at 11:27:20 UTC. This immutable revision, rather than a moving branch, is the proposed integration input.

The actual pinned [LICENSE](https://github.com/Ventusltd/pandapower/blob/109416d25abb77d75bd3622d7492e1db57ae678e/LICENSE) contains BSD-3-Clause terms and credits University of Kassel, Fraunhofer IEE and contributors. GitHub's API classifies it as `NOASSERTION`; that classifier is not evidence that the inspected licence text is absent. Preserve notices and the licence when reusing covered code, and review individual network datasets separately.

## Current status

[The adapter configuration](https://github.com/Ventusltd/sld/blob/main/config/pandapower-adapter.json) is a **proposed contract**, including a JSON Schema for future output. No pandapower adapter has been implemented or executed by this integration research. No repository clone, network model execution, symbol approval or additional furnace run is claimed. The existing furnace receipt compares declared component bounding boxes; it establishes neither electrical connectivity nor BS/IEC symbol conformity.

## Deterministic mapping

Mappings below target keys already present in `data/library.json`. They express candidate equipment semantics, not approved symbol geometry.

| Source table/field | Candidate representation | Required handling |
|---|---|---|
| `bus.type=b` | `BUSBAR_SECTION` | Preserve source bus ID, `vn_kv` and `in_service`. A drawing primitive is separate from the electrical node. |
| `bus.type=n` | `NODE` | Preserve node identity; do not fuse buses merely because drawings overlap. |
| `bus.type=m` or unknown | Unresolved | The source calls `m` a muff; this library has no verified matching component. |
| `line` | Routed polyline, no invented `LINE` component key | Electrical endpoints are `from_bus` and `to_bus`. Preserve length, parameter units and service state. |
| `trafo` | `TWO_WINDINGS_TRANSFORMER` | Electrical endpoints are `hv_bus` and `lv_bus`; preserve winding identity and ratings. |
| `trafo3w` | `THREE_WINDINGS_TRANSFORMER` | Preserve `hv_bus`, `mv_bus`, `lv_bus`; do not infer winding roles from screen position. |
| `switch.type=CB` | `BREAKER` | Explicit OPEN/CLOSED state from `closed`. |
| `switch.type=DS` | `DISCONNECTOR` | Two electrical terminals despite the source drawing's one graphical anchor. |
| `switch.type=LBS` | `LOAD_BREAK_SWITCH` | Preserve switch identity and operating state. |
| `switch.type=LS`, missing or unknown | Unresolved | A load switch must not silently become a load-break switch. |

Evidence: pinned [bus creation](https://github.com/Ventusltd/pandapower/blob/109416d25abb77d75bd3622d7492e1db57ae678e/pandapower/create/bus_create.py), [line creation](https://github.com/Ventusltd/pandapower/blob/109416d25abb77d75bd3622d7492e1db57ae678e/pandapower/create/line_create.py), [transformer creation](https://github.com/Ventusltd/pandapower/blob/109416d25abb77d75bd3622d7492e1db57ae678e/pandapower/create/trafo_create.py), and [switch creation](https://github.com/Ventusltd/pandapower/blob/109416d25abb77d75bd3622d7492e1db57ae678e/pandapower/create/switch_create.py).

`switch.et` chooses the target table: `b` bus, `l` line, `t` two-winding transformer, `t3` three-winding transformer. `switch.element` is that table's index; `switch.bus` identifies the attached bus. For a branch switch, match that bus to exactly one branch endpoint. Reject missing or ambiguous matches.

With a single branch-end switch, construct an explicitly marked synthetic connectivity node between switch and branch terminal, preserving the source attachment. Multiple switches on the same endpoint do not supply a reliable physical series ordering; retain them as unresolved rather than inventing a bay. For bus-bus switches, preserve both source buses and switch terminals. In analysis, a closed ideal bus-bus switch can fuse buses; a nonzero `z_ohm` has different semantics. Do not erase the switch from the drawing model or treat every closed switch as an ideal short.

## Next executable gate

Use stable dataset/table/index identifiers and retain all source references. The schema separates equipment, electrical terminals, connectivity nodes and unresolved findings. Graphical anchor bindings remain null pending review. Referential integrity, unique IDs, endpoint cardinality and type-specific mapping need procedural validation in addition to JSON Schema; a schema pass alone cannot establish topology correctness.

Build independent synthetic fixtures for bus-bus CB open/closed, line-end DS, transformer-end LBS, three-winding endpoints, nonzero switch impedance, unsupported LS and ambiguous attachment. Compare connected components before/after switching against an independent graph implementation. Keep those topology results separate from GPU geometry results and from any power-flow calculation.

Known BS/IEC symbol comparison requires an authorised reference corpus with standard/reference identifiers, symbol function, terminal conventions, drawing revision and reviewer. The current PowSyBl candidates remain unverified. Every production part still requires the approved real-project drawing issued after 2012 and engineering review. GPU similarity or agreement cannot supply that missing evidence.
