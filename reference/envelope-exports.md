# Simplified envelopes for factory layout

Use this export when a machine must be placed in a floor plan, combined with
other equipment, checked for service space, or connected to material flow.
A detailed mechanical STEP often carries thousands of irrelevant faces and
holes. An envelope should load quickly while conservatively reserving the
space that matters to placement.

## Source and shape policy

Treat envelopes as another config-driven artifact family. Reuse the machine's
origin, floor datum, units, bay/module positions, motion limits and selected
geometry. Derive from the verified assembly or its exact bounding information;
check its source hashes before exporting. A tessellated mesh can understate
curved extents, so it is not an exact bounding oracle without an error allowance.

Use a small number of boxes, cylinders or simple extrusions. Keep separate
transport bays or height regions when one large bounding box would hide useful
access, such as open robotic loading ends. Simplification may fill irrelevant
internal voids, but should not invent clearance where equipment exists. Round
extents outward, not to the nearest value. Make padding and size/complexity
budgets configurable when the consuming layout workflow needs them.

Keep these meanings explicit in names, groups and the manifest:

- **Installed occupancy:** conservative bounds of the modeled equipment,
  including projecting handles, fasteners and moving hardware where relevant.
- **Planned occupancy:** reserved but unselected conveyors, robots, carts or
  stations. State whether the primary machine envelope includes them.
- **Service/access:** doors, withdrawal paths, operator aisles, maintenance and
  overhead work zones. Export separately from equipment; they can overlap
  installed or moving equipment by design.
- **Flow/interfaces:** input/output transfer targets, direction vectors, heights,
  and located utility connections. Mark a point as measured, selected or
  provisional. Use null/unlocated status for connections that are not known.
- **Transport:** a separately labeled stripped configuration, when useful.
  Record what is removed and the transform back to installed coordinates.

Do not promote a layout allowance into a regulatory clearance, robot reach
solution or connector specification. If existing reservations conflict, record
the conflict; do not silently move equipment just to make the export look clear.

## Portable output set

Choose formats for the user's layout application. A practical default is:

| Artifact | Meaning |
|---|---|
| `MachineEnvelope.step` | Small set of named machine occupancy solids |
| `MachineEnvelope.FCStd` | Same simplified geometry with editable group visibility |
| `ServiceClearances.step` | Separate access and withdrawal volumes |
| `AncillaryEnvelope.step` | Separate carts/utilities, when present |
| `SiteEnvelope.step` | Explicit combined planning variant, if helpful |
| `FactoryLayout.dxf` | Closed XY outlines on named layers; arrows/labels separately |
| `envelope-manifest.json` | Bounds, sources, coordinate frame, interfaces and checks |

SVG/PNG or a small offline HTML preview makes the result reviewable without a
CAD installation. Keep clearance and planned-equipment visibility independent.
The preview is not a substitute for the actual CAD/DXF artifact.

Use a separate envelope config or a namespaced section in the assembly config;
avoid copying dimensions into a second manually maintained model. For example:

```yaml
envelope_export:
  enabled: true
  units: mm
  source_revision: assembly-r012
  round_outward_mm: 1
  machine_categories: [installed, motion, planned_conveyor]
  separate_categories: [service, utility_cart, interfaces]
  max_step_bytes: 1000000
  flow_targets:
    - id: material_in
      position_ref: conveyor.entry_datum
      direction: [1, 0, 0]
      status: provisional
```

The concrete schema belongs to the project. Prefer references or derivations
from existing datums over duplicate XYZ values. Distinguish an independent
export revision from its source assembly revision so changing export detail
does not imply changing the physical machine.

## Acceptance checks

Verify what the simplified artifact claims:

1. Source assembly/config hashes and prior checks are current.
2. Every included physical component lies inside the designated occupancy
   solids. Conservative bounding-box containment is sufficient when valid;
   use an exact residual check for tighter or non-box shapes. Account for
   moving sweeps and projecting hardware, including omitted modeled detail.
3. Important openings and differences between installed, service and transport
   variants survive simplification.
4. STEP round trips retain valid solids, extents, placement and units. Check
   file size and solid/face counts against the intended lightweight budget.
5. DXF units, layer membership, closed outlines and flow-point positions round
   trip at the same origin and scale. Put labels/arrow geometry on separate
   layers so it cannot be mistaken for occupied floor area.
6. Known interface directions are unit vectors, and each coordinate has a
   documented frame and status. Unknown connections remain unlocated.
7. Render and inspect the primary envelope and floor-plan view. Verify any
   preview layer controls and links to exported files.

Record measured bounds, counts, file hashes, source-to-export transforms and
unresolved layout conflicts in the manifest. Commit config, generator and
curated exports using the project's existing artifact convention. Publishing
or pushing the skill/project still follows the user's authorization scope.
