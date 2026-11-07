# Getting started

CAD as Code has two related workflows: generate verified geometry from config,
and generate illustrated work instructions from existing geometry plus an
authored process. You can use the scripts directly or install the
[skill](../SKILL.md) in an agent that supports it.

## Choose your starting point

| You want to… | Start with… | What you need |
| --- | --- | --- |
| View an existing work package | Open its `index.html` or PDF | The complete revision folder; no Python, FreeCAD, account or server |
| Generate a first CAD part | The arbor template below | FreeCAD 1.x |
| Author instructions for a machine | The instruction pipeline below | Your machine's CAD, BOM, config and process requirements |
| Read the reusable process contract | [Build-process schema](../schemas/build-process-v1.json) and [workflow reference](../reference/work-instructions.md) | No machine checkout |
| Rebuild the real fly-winder pilot | Its consuming project's `docs/work-instructions-pilot.md` | A separate `stator-winder/fly` checkout and its exact CAD inputs |

The fly-winder models, process definitions and generated guides are **not** part
of this repository. A clean clone does not contain a prebuilt work package or a
self-contained work-instruction machine example. The bundled arbor example is
a CAD-generation example. The general instruction tools work with your own
FreeCAD assembly; they do not require fly-winder geometry or a FactoryOS service.

## First CAD run

From the repository root, on macOS with FreeCAD installed in `/Applications`:

```sh
cd templates
./run.sh
```

The runner defaults to FreeCAD's `freecadcmd`. Set `FREECADCMD` to your installed
executable on another platform. It prints geometric checks and `RESULT PASS`,
and writes an FCStd, STEP and manifest under
`templates/output/arbor/<SKU>/rNNN/`. Read
[output conventions](../reference/output-convention.md) before changing the
template or publishing its outputs. See the
[stator-jig example](../examples/stator-jig/README.md) for multiple input configs.

Run the remaining commands from the repository root, not `templates/`.

## Install the instruction tooling

The instruction compiler and the CAD adapter use separate Python environments.
The tested setup uses Python 3.12 for the compiler and the Python bundled with
FreeCAD 1.1.3 for geometry extraction.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-instructions.txt
```

| Stage | Additional prerequisite |
| --- | --- |
| Extract CAD geometry | A Python interpreter that can import `FreeCAD` and `Part`; the commands below use FreeCAD's macOS bundle |
| Compile HTML/PDF | The `.venv` dependencies above and an authored process JSON |
| Verify offline HTML | Chromium installed for Playwright: `.venv/bin/python -m playwright install chromium` |
| Check PDF references | Poppler's `pdftotext` on `PATH` |
| Visually inspect print pages | Poppler's `pdftoppm` on `PATH` |

The geometry script is read-only: it copies shapes and checks the FCStd hash
before and after extraction. It does not save the model. On another platform,
use your FreeCAD-enabled Python interpreter in place of the bundle path below.
Installing a package named FreeCAD in the compiler's virtual environment is not
part of this workflow.

## Generate work instructions for your machine

### Prepare the consuming project

Keep reusable tools in this repository and machine-specific inputs in a separate
project. For example:

```text
my-machine/
  config/work-instructions/machine-r001.json   authored process definition
  config/                                    CAD/product config
  cad/                                       existing assembly.FCStd
  docs/                                      requirements and source references
  output/work-instructions/
    cache/                                   extracted presentation geometry
    my-machine/r001/                         generated offline package
    qa/r001/                                 browser reports and page renders
    build-records/                           execution records, kept separately
```

Author a JSON definition against
[`schemas/build-process-v1.json`](../schemas/build-process-v1.json). It describes
more than assembly order:

| Field | Meaning |
| --- | --- |
| `product`, `variant`, `revision`, `status` | Product identity and draft/reviewed/released instruction revision |
| `cad_source`, `sources` | Paths relative to the consuming project, with SHA-256 of the exact CAD, config, BOM and requirement bytes |
| `parts` | Common part numbers/specifications, e.g. one definition for an M6 x 20 screw |
| `instances` | Each installed occurrence, with its own semantic ID and CAD object mapping or hardware placement |
| `datums` | Named coordinate frames/patterns; lengths are in mm |
| `packages` | Independently assignable subassembly work packages |
| `operations` | Ordered IDs, prerequisites, starting conditions, installed parts, visible context, tools, consumables, directions and checks |
| `requirements` | Sourced requirements and explicit unresolved holds |
| `bom` | Leaf quantities and reference-only context; do not count a subassembly and its leaves twice |

Within an operation, `install` consumes an instance once; `uses` selects the
instances visible in that figure, including previously installed context.
`view.offsets_mm` explodes presentation geometry without moving the authoritative
assembly. Details can have their own camera, CAD section or `crop_box_mm`.
The [workflow reference](../reference/work-instructions.md) explains those fields,
hardware verification and fabrication holds in detail.

Use `"callout_style": "grouped_by_part"` to give four identical screws labels
such as `2a–2d`, with one quantity-four common-part row. Instance IDs stay unique.
Different part numbers, including different screw lengths, remain separate.
The default `per_instance` style supports older definitions.

Compute each source hash from the actual file content, including local edits:

```sh
python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' /path/to/source
```

Do not replace a stale hash just to make a build pass. Review the changed source
and its effects, then issue a new instruction revision as appropriate. CAD
geometry does not supply missing weld sizes, torque, fit or acceptance limits.

### Extract, compile and verify

Replace the example project path and filename before running these commands.
They assume an authored `machine-r001.json` and its referenced input files
already exist. These scripts do not infer a process from an arbitrary assembly.

```sh
MACHINE_ROOT="$(pwd)/../my-machine"
PROCESS_PATH="$MACHINE_ROOT/config/work-instructions/machine-r001.json"
GEOMETRY_PATH="$MACHINE_ROOT/output/work-instructions/cache/geometry-r001.json"
PACKAGE_ROOT="$MACHINE_ROOT/output/work-instructions/my-machine"
QA_DIR="$MACHINE_ROOT/output/work-instructions/qa/r001"
FREECAD_PYTHON="/Applications/FreeCAD.app/Contents/Resources/bin/python"

mkdir -p "$(dirname "$GEOMETRY_PATH")" "$QA_DIR"

"$FREECAD_PYTHON" tools/instruction_geometry.py \
  "$PROCESS_PATH" "$MACHINE_ROOT" "$GEOMETRY_PATH"

.venv/bin/python tools/work_instructions.py "$PROCESS_PATH" \
  --root "$MACHINE_ROOT" --geometry "$GEOMETRY_PATH" --out "$PACKAGE_ROOT"

.venv/bin/python tools/verify_instruction_package.py "$PACKAGE_ROOT/r001" \
  --report "$QA_DIR/offline.json"

pdftoppm -scale-to 1200 -png "$PACKAGE_ROOT/r001/work-instructions.pdf" \
  "$QA_DIR/page"
```

Inspect the rasterized PDF pages and enlarge hardware/joint SVGs. The verifier
checks `file://` operation with networking disabled, figure and BOM links,
callout consistency, PDF references and artifact hashes. It does not establish
physical fit, weld qualification or inspection acceptance.

### Open or share the result

The compiler writes `PACKAGE_ROOT/r001/` using the revision in the authored
definition:

| Output | Use |
| --- | --- |
| `index.html`, `figures/*.svg` | Offline navigation and enlarged illustrations |
| `work-instructions.pdf` | Printable guide with matching operation/figure numbers |
| `process.json`, `bom.json`, `callouts.json` | Machine-readable process, quantities and bubble-to-instance mappings |
| `manifest.json`, `sources/`, `generators/` | Exact source/compiler snapshots and content hashes |
| `geometry.json`, `review-impact.json` | Presentation cache and operations needing review |

Copy the **whole revision directory** to another computer for offline HTML;
copying `index.html` alone loses its figures. The PDF can be shared by itself.
These are generated artifacts and are ignored by Git here. Keep authored process
and CAD generator/config sources in the consuming project's version control.

Allocate `r002` when inputs or the compiler change. Re-extract the geometry cache
after changing instance mappings, placements, section planes or cropped details.
Pass `--previous "$PACKAGE_ROOT/r001"` to the compiler for review impact.
An unchanged run can reuse a revision; different content cannot overwrite it.
Keep prior packages and build records. A build already in progress stays pinned
to its original instruction digest.

For a smaller PDF to send, use `tools/compact_instruction_pdf.py` with an output
path outside the pinned revision folder. It keeps the original intact and writes
a derivative manifest; see [sharing export](../reference/work-instructions.md#smaller-pdf-for-sharing).

`tools/build_records.py --help` describes the local event import/export mock.
It keeps completion distinct from inspection acceptance. FactoryOS identifiers
and events remain a proposed integration boundary, not deployed endpoints.

## Checks you can run

This standalone check works with a clean clone after installing the Python
requirements; it needs neither FreeCAD nor the fly-winder checkout:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_instruction_rendering.py' -v
```

The full pilot integration suite currently reads machine definitions and
geometry caches from `../stator-winder/fly`. Some checks need its generated
`output/work-instructions/cache/geometry-r006.json`; other tests use earlier
instruction revisions. Follow that project's `docs/work-instructions-pilot.md`
to prepare those inputs before running:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

A missing sibling checkout is not a prerequisite failure for the reusable
renderer. The integration suite is not currently a clean-clone standalone suite.
The [pilot verification report](work-instructions-verification.md) records the
actual tested scope and known limitations.

## Common first-run issues

| Symptom | What to check |
| --- | --- |
| `No module named FreeCAD` | Run geometry extraction with FreeCAD's Python, not the compiler's `.venv` interpreter |
| Missing source or `Stale source hash` | Check `--root`, project-relative paths, exact file bytes and the intended baseline |
| Stale geometry, mapping, section or detail cache | Re-extract using the same process definition you will compile |
| `Immutable revision exists with different content` | Keep the prior directory and author a new `rNNN`; compiler edits also change instruction identity |
| Playwright cannot find Chromium | Run the browser installation command above in the same `.venv` |
| `pdftotext` / `pdftoppm` not found | Install Poppler and put its executables on `PATH` |
| HTML opens without illustrations | Restore the revision's `figures/` directory beside `index.html` |
| Mandatory hold prevents release | Resolve the sourced engineering requirement; a valid CAD solid does not resolve it |

For implementation decisions, read
[ADR 0001](decisions/0001-illustrated-work-instructions.md). For the CAD workflow,
continue with [repository layout](../reference/repo-layout.md),
[FreeCAD/headless recipes](../reference/freecad-headless.md), and
[verification patterns](../reference/verification.md).
