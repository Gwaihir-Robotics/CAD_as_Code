# ADR 0001: Authored process, read-only CAD adapter, immutable instruction packages

2026-11-06. Implemented pilot; manufacturing release remains blocked.

Keep the reusable JSON Schema, compiler, FreeCAD geometry adapter, offline verifier
and local event adapter here in CAD_as_Code. Keep part mappings, requirements,
operation sequence and sample build data in `stator-winder/fly/config/work-instructions/`.
Existing CAD macros and the hardware BOM remain authoritative design inputs.
Do not fork the geometry generator to author instructions.

The adapter opens the existing FCStd read-only, copies shapes and exports world
meshes, per-instance BREP fingerprints, cylinder-axis hardware checks and candidate
joint locations. Semantic instance IDs map to explicit CAD object names plus
source hashes. Datums name coordinate frames and mounting patterns; no face
indices are persisted. Authored process information is never written into CAD.
SVG projection applies explosion offsets to presentation points only. The source
FCStd hash is checked before and after extraction. This lightweight vector mesh
renderer uses depth sorting, not an exact hidden-line solver; ambiguous overlaps
require a different camera or a dedicated close-up. Fastener geometry is a
nominal dimensional envelope, not a supplier-detailed thread/socket model.

Compile one authored definition to SVG, local HTML, ReportLab PDF, process/BOM
JSON and a content-addressed manifest. Snapshot exact input bytes, including
uncommitted edits. Allocate a new revision on any process or compiler change;
refuse to overwrite a different existing revision. Stage new output before an
atomic directory rename. Build records live outside instruction directories.
Existing packages work offline without FreeCAD or Python.

On regeneration compare operation definitions, leaf-instance shape hashes,
part definitions, datums, requirements and referenced sources. Propagate review
through explicit prerequisites. Conservatively invalidate all operations when
non-CAD process inputs change; this favors review over a falsely precise impact
claim. A changed CAD/config interface is therefore caught even if the visible
solid stays identical. No automatic release or physical process qualification.

FactoryOS currently has architecture and requirements, not deployed endpoints
(README, architecture, requirements, roadmap, TDP-to-inspection design inspected).
Match its separation of intent, approved process, actual execution and disposition.
Use a local SQLite outbox and file import/export first. The assembly event names
and envelope in this extension remain proposals. FactoryOS adoption requires a
separate contract review; there is no dependency on a live service.

Dirac's BuildOS platform is inspiration for geometry-linked instructions and
feedback, not an API or implementation dependency: https://www.diracinc.com/platform
Static figures keep this pilot auditable and portable. Interactive 3D and
animation can later consume the same instance and operation definitions.
