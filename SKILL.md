---
name: cad-as-code
description: Build and evolve CAD as version-controlled, parametric FreeCAD generator macros driven by config (YAML / PARAMS dict / spreadsheet), run headless, verified by scripted checks, with regenerable outputs. Load whenever the user asks for a CAD part, fixture, jig, plate, bracket, arbor, or assembly; wants to change a dimension in an existing generator; asks about FreeCAD/OCC scripting; asks how to make CAD work with a coding agent; or wants simplified machine envelopes for factory layout, access clearances, or material-flow interfaces. Also load for config-driven SVG electrical/component visualizations of industrial machinery (PLC/control panels, drives, field I/O and machine utilities), not general electronics or PCB design. Also load before touching any *.FCMacro, output/ or generated/ folder.
license: MIT
---

# CAD as Code (a.k.a. CAD as Config)

You are not a CAD operator. You are the author of a **generator**: a headless
FreeCAD macro that reads **config** and writes **geometry**, plus the **checks**
that prove the geometry is right. Treat every request for "a part" as a request
for a program that produces that part.

The pattern is config-as-code borrowed from infrastructure (Kubernetes):

| Infra | CAD as Code |
|---|---|
| manifest (`deployment.yaml`) | config: YAML file, `PARAMS` dict, or FreeCAD `Params` spreadsheet |
| controller / reconciler | the generator macro (`*.FCMacro`) |
| live cluster state | `output/<family>/<SKU>/<rev>/` (FCStd, STEP, DXF, PNG) + `cad-manifest.json` — regenerable, never hand-edited |
| `kubectl apply` | `freecadcmd macros/Foo.FCMacro` |
| readiness probe | verification script: residuals, interference, symmetry, clash |
| CRD | the config keys a generator promises to consume |

## Opening an existing model

For requests such as "show me the assembly in FreeCAD" or "open the model",
open the existing `.FCStd` directly with the operating system's file launcher.
On macOS, use `open -a FreeCAD "/absolute/path/to/model.FCStd"`.
Use its saved view; do not invoke Computer Use, rebuild the model, or run the
modeling workflow just to display a file. Reserve Computer Use for requested UI
interaction that cannot be handled through FreeCAD's CLI or macros.

## The one rule you must say out loud

**You cannot model an airliner from a sentence.** If the request is a machine,
an assembly, or "a bracket for X" with no datums, do not start modelling.
Decompose first, and tell the user you're doing so:

1. Identify the parts. One generator per part family (plate, arbor family, jig).
2. Pin the **frame**: origin, +Z, which face is "front", units. Write it into
   the macro docstring.
3. Get **ground truth**: vendor STEPs, measured datums, an existing DXF. Measure
   them with code (`Shape.BoundBox`, `slice`, `Faces` with cylinder surfaces).
4. State the **acceptance check** for each part in one sentence. If you can't,
   the ask is still too big.

Only then write the generator.

## Workflow

### 0. Orient
- Look for an existing generator (`macros/*.FCMacro`, `*Generator*`) and its
  config before writing anything. Extend; don't fork.
- Read `reference/repo-layout.md` for the expected tree; create it if absent.
- Check project memory for measured datums and known OCC workarounds.

### 1. Config first
- Every dimension the user might change is a named parameter with a comment
  and unit. Group: `COMMON`, then per-part dicts, or a YAML file
  (see `reference/config-schema.md`).
- If a shared product config exists (e.g. a stator YAML), **read it**; if you
  need a new per-SKU knob, **add a namespaced key** to it (`side_guide.tip_gap`)
  with a comment naming the consumer, using an **idempotent** writer.
- Machine-level constraints become single numbers the generator derives from
  (e.g. `center_height` constant across SKUs).

### 2. Generator
- Headless-safe: works under `freecadcmd`; GUI-only calls guarded by
  `App.GuiUp`. See `reference/freecad-headless.md`.
- Build with `Part` primitives + booleans; slice vendor STEPs for profiles
  rather than describing them.
- Placement: compose (`pose.multiply(obj.Placement)`), never overwrite, for
  imported multi-solid parts.
- Save to `output/<family>/<SKU>/<rev>/`: FCStd **and** one STEP per part
  (`<id>-<part>.step`) **and** `cad-manifest.json` with the config sha and
  resolved params (`reference/output-convention.md`). Write `GuiDocument.xml`
  so headless saves open visible. Delete-and-recreate objects; `purgeTouched()`.
- Follow `reference/occ-workarounds.md` when booleans/offsets/STEP misbehave.
- Encode DFM as parameters/rules, not prose (`reference/dfm-checklist.md`).

### 3. Verify — non-negotiable
Every generator ends by printing checks that a human can read as pass/fail
(see `reference/verification.md`):
- boolean residual (cutter ∩ result volume == 0.0),
- interference between mating parts (== 0 or == the intended seat volume),
- symmetry residual when a part is claimed L/R-interchangeable,
- expected-hole audit (cylindrical faces at expected XY/Ø),
- fixture/keep-out clash per SKU,
- STEP round-trip is a solid.
Print numbers, not adjectives. Do not claim success in prose you have not
measured.

### 4. Iterate on pictures
Render (`render_views.FCMacro`-style GUI macro, or `saveImage`) and look.
Map the user's human feedback ("wrong axis", "leg should fold the other way")
onto parameters. Re-run, re-render, re-check.

### Factory-layout exports (when relevant)
For machine placement, floor plans, service space or material-flow integration,
export a lightweight envelope alongside the detailed CAD. Read
[reference/envelope-exports.md](reference/envelope-exports.md): derive conservative
solids from verified geometry/config, keep equipment and clearance volumes
separate, preserve units/origin and flow datums, and label unselected interfaces.
This is an optional output mode for assemblies, not a requirement for every part.

### Industrial electrical visualization (when relevant)
For an industrial machine's PLC/control panel, drives, field I/O, power paths or
machine utilities, read
[reference/industrial-electrical-svg.md](reference/industrial-electrical-svg.md).
Generate a config-driven SVG component view with optional offline HTML layer
controls, using the project's component tags and electrical relationships.
Preserve existing schematics; keep selections and proprietary artifacts in the
project. This mode complements mechanical CAD and uses topology/SVG/browser
checks rather than FreeCAD solid checks. It does not cover general electronics
or PCB design.

### Illustrated work instructions (when relevant)
For assembly, weldment fabrication or BOM-linked visual work packages, read
[reference/work-instructions.md](reference/work-instructions.md). Keep authored
process definitions in the consuming project; use the reusable schema/compiler
here. Pin exact source content, separate part numbers from installed instances,
preserve immutable instruction revisions and build records, and retain unknown
manufacturing requirements as release-blocking holds. CAD validity alone does
not release a fabrication procedure.

### 5. Commit
- `output/` is gitignored (reproducible via manifest sha); commit the curated
  `exports/` (vendor bundles, latest STEP per part). Never hand-edit either.
- Branch per feature. The PR is the config diff.
- Update memory with measured datums and any new workaround.

## Things that go wrong (recognise them fast)
- Keyhole/oval holes → a hole grazes a cutout edge; the generator slotted it to
  avoid a sliver. Change hole size/pattern or accept.
- Objects invisible / "recompute?" on open → missing `GuiDocument.xml`.
- STEP re-imports as a shell → `cleaned_solid`, `to_analytic`, single-plane
  slices.
- Rails / multi-solid imports scrambled → you overwrote per-solid Placement.
- FreeCAD shows old geometry after regen → close and reopen the FCStd.
- Config file grows duplicate headers → your append wasn't idempotent.

## Bundled references
- `reference/repo-layout.md` — folder conventions
- `reference/industrial-electrical-svg.md` — industrial machine power/control topology, layered SVG reviews and verification
- `reference/envelope-exports.md` — lightweight machine/site STEP, layered floor-plan DXF, flow datums and containment checks
- `reference/output-convention.md` — output/<family>/<SKU>/<rev>/, cad-manifest.json, hybrid git policy
- `reference/config-schema.md` — YAML/PARAMS/spreadsheet conventions, idempotent writers
- `reference/freecad-headless.md` — freecadcmd, saving, visibility, STEP I/O, spreadsheets, rendering
- `reference/occ-workarounds.md` — battle-tested fixes for OCC/FreeCAD edge cases
- `reference/verification.md` — check patterns with code
- `reference/dfm-checklist.md` — sheet metal, casting, machined, printed
- `templates/` — generator skeleton, config example, verify macro, run script (run `templates/run.sh` to see a PASS)
- `examples/stator-jig/` — trimmed real example (stator YAML → arbor)
- `blog/cad-as-config.md` — the long-form write-up
