# Illustrated assembly and fabrication work instructions

Use this module when extending CAD-as-config into an offline work package.
Reusable code lives in `tools/`, schemas in `schemas/`; authored process JSON and
build examples belong to the consuming machine repository. Never infer weld,
torque, adhesive, fit or lubricant requirements from geometry. A missing source
or mandatory requirement is a hold, not a plausible default.

New to the repository? Start with [Getting started](../docs/getting-started.md)
for environment setup, the extraction/compilation commands and a guide to the
generated files. This reference describes the authoring contract in more detail.

## Contract and lifecycle

`schemas/build-process-v1.json` validates product/variant/revision, named sources
with SHA-256, stable part numbers, installed leaf-instance IDs, datums, assignable
subassembly packages, ordered operations/prerequisites, installed and context
parts, tools/consumables, illustrations and inspection checks. `uses` is the
visible callout set; `install` accounts for consumption once. Reference-only
shared parts are explicitly excluded from consumption. Never count a
subassembly container as well as its installed leaves.

Set optional `callout_style: "grouped_by_part"` in the consuming process JSON
to use one bubble number per common part number. Repeated locations receive
suffixes (`2a`, `2b`, `2c`, `2d`); a single location keeps its bare number.
Bubble numbers are local to an operation, and detail views retain the full
parent operation key, even when they hide other parts. Suffixes follow authored
instance order; changing the camera never renumbers them. Group by the exact
part ID, so M6 x 20 and M6 x 30 cannot merge just because they share a thread.
The default `per_instance` retains legacy numbering; manual `callout_numbers`
overrides cannot be mixed with grouped mode.

HTML/PDF callout keys show the common part, quantity shown and location range;
expanded location rows preserve semantic installation IDs and placement checks.
`callouts.json` exports the same labels and instance mappings. Shown quantities
include reference/context parts and do not replace per-operation installation
quantities or the overall BOM. The latter retain their existing accounting.

Each hardware instance requires an explicit placement (seat, axis, target CAD
object, semantic pattern datum and verification state). The FreeCAD adapter
checks matching analytic cylinder axes without storing face numbers. This is
axis verification, not proof of thread engagement, strength or installation
access. Candidate servo hardware stays incomplete and blocks release. Source
hardware role/diameter/length and allocated quantities are checked. Thread and
socket graphics are omitted from nominal screw envelopes.

`instruction_geometry.py` uses FreeCAD's bundled Python. It reads FCStd solids,
exports presentation meshes/BREP fingerprints and candidate contacting tube
pairs within 0.3 mm. Candidate joints are identified by the two semantic member
IDs, with measured witness locations; they are not weld requirements or a
complete qualified joint schedule. Include authored weld source, fixture/tack
sequence and inspection tolerances before resolving a weld hold.

`work_instructions.py` validates cross-references, topological operation order,
unique consumption, BOM counts, placement audits and source bytes before
publishing. Presentation offsets never modify placements. Consistent cameras,
current/prior/hardware colors, scale bars, callout keys and a triad are shared by
HTML and PDF. Author close-ups by selecting only the relevant `uses`, camera and
offsets; hide future/obscuring parts. Review each figure before use. The
renderer supports static exploded/assembled views and authored detail sections.
A detail `view.section` specifies normal and plane distance in mm; the FreeCAD
adapter slices authoritative solids into actual section contours (Figure 2A
in the pilot). Sections omit solids away from the selected plane.

For local joint close-ups, author a detail `view.crop_box_mm` containing
`[xmin, ymin, zmin, xmax, ymax, zmax]` in the assembly world datum, in mm.
The FreeCAD adapter intersects copied solids with that box and tessellates them
at 0.05 mm deflection so small dogbone reliefs remain visible. The base geometry,
placements and part hashes remain intact. Apply `offsets_mm` after the crop to
show local exploded tab/slot fits. Crop boundaries and explosion distances are
presentation aids, not new cut lengths or fabrication requirements. The cache
records exact detail IDs, crop boxes and source instances; stale crops reject.

Illustrations use solid medium-grey context, saturated blue current parts and
amber hardware, with directional shading and thin mesh-derived crease/silhouette
outlines. Keep the context readable against white paper; reduced emphasis should
not wash out holes and mating surfaces. Coplanar tessellation diagonals are
suppressed. Edges participate in surface depth sorting; this remains an
approximate mesh renderer rather than exact CAD hidden-line removal. A compiler
style change marks all operations for visual review in a new immutable revision.

Draft, reviewed and released are explicit. A mandatory open requirement or an
incomplete visible hardware placement blocks package release; release also
requires a reviewer identity. This local metadata gate does not authenticate
signatures or qualify a manufacturing process. `review-impact.json` lists all
affected operations and downstream prerequisites. A definition marked as needing
review must be reviewed by engineering before an external release workflow.

Revision directories are immutable. Same content is reusable; changed content
requires a new `rNNN`. Manifests include config, CAD, BOM, generator and schema
hashes. Full exact source snapshots identify dirty worktree bytes independently
of Git. Preserve old directories and build records; never repin a running build.
Caches must be rebuilt after instance mappings or placements change.

## Rebuild the fly pilot

See the consuming project's `docs/work-instructions-pilot.md` for baseline and
commands. Installation from this repository:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements-instructions.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python -m unittest discover -s tests -p 'test_instruction_rendering.py' -v
```

The command above runs the standalone renderer checks. The complete test suite
also needs the separate fly-winder checkout and its prepared geometry caches;
see [testing prerequisites](../docs/getting-started.md#checks-you-can-run).

Author the process first. Run the read-only geometry adapter, then compile and
verify. Pass `--previous /path/to/r001` when compiling r002. Inspect rasterized
PDF pages and enlarged hardware SVGs. The browser verifier uses `file://` with
network offline; no server, account, CDN, remote fonts or script is needed.

## Execution boundary

`build_records.py` stores append-only events and a durable pending outbox in
SQLite (WAL + FULL synchronous). Export pending events to a file, retry exports
until acknowledged, import idempotently at the mock receiver, then import
acknowledgements. It increments attempt counts; scheduling/backoff and network
transport are deliberately deferred. Duplicate IDs with changed contents reject.
Corrections use a new event with a reference to earlier evidence; never edit
prior events. There are no browser checkboxes. Explicit exported files and the
SQLite database are local records requiring backups; they do not synchronize
or authenticate themselves. Manufacturing authorization is outside this mock.

## Smaller PDF for sharing

This exporter needs Playwright Chromium and Poppler’s `pdftotext` installed.
Keep the pinned vector package as the authoritative artifact. For a smaller
copy to send, rasterize the CAD figures while retaining selectable/searchable
instruction text and figure labels:

```sh
.venv/bin/python tools/compact_instruction_pdf.py /path/to/package/r006 \
  --out /path/to/sharing/work-instructions-r006-compact.pdf
```

The output must be outside the immutable package and must not already exist.
The exporter verifies source hashes and compares extracted text before writing
its derivative PDF/manifest. Graphics are approximately 220 dpi JPEGs; text and
page layout remain unchanged. Inspect the result before sharing. This is an
optional derivative, not a new instruction revision or a manufacturing release.
