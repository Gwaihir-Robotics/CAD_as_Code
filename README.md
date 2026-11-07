# CAD as Code

**Git-backed, parametric CAD with a coding agent.** A reusable skill plus the
reference material behind Gwaihir Robotics' way of building fixtures, jigs and
machine plates: FreeCAD generator macros driven by config (YAML / PARAMS /
spreadsheet), run headless, verified by scripted checks, outputs regenerable —
config-as-code borrowed from Kubernetes and applied to CAD.

Read the series on gwaihirrobotics.com:

1. [CAD as Config](https://gwaihirrobotics.com/blog/2026-08-cad-as-config) — the original generator/config workflow ([repo copy](blog/cad-as-config.md)).
2. [CAD as Config, two months on](https://gwaihirrobotics.com/blog/2026-10-cad-as-config-two-months-on) — the follow-up on motion, procurement and factory layout.
3. [CAD as Config, part 3: work instructions](https://gwaihirrobotics.com/blog/2026-11-cad-as-config-work-instructions) — illustrated assembly/fabrication guides, grouped callouts and build feedback ([repo copy](blog/cad-as-config-work-instructions.md)).

## Start here

Read [Getting started](docs/getting-started.md) for prerequisites, a first CAD
run, and the path from an existing assembly to illustrated instructions.
The command-line tools can also be used without an agent.

- **Generate a part:** start with the [template](#try-the-template-needs-freecad-1x).
- **View an instruction package:** copy the whole revision folder and open
  `index.html` or `work-instructions.pdf`; no CAD software or server is needed.
- **Author assembly/fabrication instructions:** follow the
  [work-instruction quickstart](docs/getting-started.md#generate-work-instructions-for-your-machine)
  and [workflow reference](reference/work-instructions.md).

## The honest premise

You cannot ask an agent for "a CAD model of an airliner." What works is
decomposing to parts, pinning frames and datums, feeding vendor geometry as
ground truth, and asking the agent for a **generator** plus the **checks** that
prove it — then iterating on screenshots and committing config, generator and
outputs together. Details in [`SKILL.md`](SKILL.md).

## Install the skill

```sh
git clone https://github.com/Gwaihir-Robotics/CAD_as_Code.git ~/code/CAD_as_Code
mkdir -p ~/.claude/skills && ln -s ~/code/CAD_as_Code ~/.claude/skills/cad-as-code
```
Claude Code loads `SKILL.md` (frontmatter `name: cad-as-code`) and can read the
`reference/` files it points to. Project-local install: symlink into
`<repo>/.claude/skills/cad-as-code` instead.

## Try the template (needs FreeCAD 1.x)

```sh
cd templates && ./run.sh                     # builds an arbor from config.example.yaml, prints checks, PASS
cd ../examples/stator-jig && CONFIG=configs/stator_32mm_12n.yaml OUT_DIR=generated \
  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd arbor_from_stator.FCMacro
```

## Contents

```
SKILL.md                    the skill: rules, workflow, failure modes
reference/
  repo-layout.md            macros/ docs/ generated/ external_imports/ exports/ tools/
  config-schema.md          YAML vs PARAMS vs spreadsheet; idempotent writers
  freecad-headless.md       freecadcmd, saving, GuiDocument.xml, STEP I/O, rendering
  occ-workarounds.md        slice/fuse silhouettes, offsets, slots, cleaned_solid, placement…
  verification.md           residual / interference / symmetry / hole audit / clash / round-trip
  envelope-exports.md       lightweight factory STEP, layered floor plans, flow datums and clearances
  work-instructions.md      authored process, grouped bubbles, close-ups, revisions and build records
  dfm-checklist.md          sheet metal, casting, machined, fixtures, interchangeability
docs/
  getting-started.md        newcomer setup, CLI pipeline, outputs, tests and troubleshooting
  decisions/               architecture decisions
schemas/
  build-process-v1.json     versioned build-process configuration contract
tools/
  instruction_geometry.py  read-only FreeCAD adapter, sections and cropped joint geometry
  work_instructions.py     process + geometry → offline SVG/HTML/PDF and revision manifest
  verify_instruction_package.py  offline browser, figure/key and artifact-hash checks
  build_records.py         local event import/export mock; no live FactoryOS dependency
  compact_instruction_pdf.py  smaller sharing PDF; original package kept intact
requirements-instructions.txt   Python dependencies for instruction tools
tests/                      renderer checks plus separate fly-pilot integration checks
templates/
  generator_template.FCMacro  config → build → verify → FCStd + STEP (+ visibility fix)
  config.example.yaml
  verify_template.FCMacro     standalone STEP checks over generated/
  run.sh
examples/stator-jig/        trimmed real stator configs + arbor runner
blog/                       the post and its (regenerable) images
```

MIT licensed. Issues and PRs welcome — especially new OCC workarounds with a
reproducer.

## Illustrated work instructions

The compiler turns authored operations and existing CAD into an offline guide,
printable PDF, BOM/instance callout data and a manifest with exact source hashes.
It supports grouped common-part bubbles (`2a–2d` for four identical screws),
exploded views, CAD sections and cropped dogbone/tab-slot close-ups. Unknown
fabrication requirements remain explicit holds.

Start with the [newcomer guide](docs/getting-started.md), then use the
[workflow module](reference/work-instructions.md),
[schema](schemas/build-process-v1.json) and
[architecture decision](docs/decisions/0001-illustrated-work-instructions.md).
Reusable tools live here; machine process definitions and build records belong
in the consuming machine project. The fly-winder pilot and its CAD files live
in a separate `stator-winder/fly` checkout and are not bundled with this repo.

The [testing instructions](docs/getting-started.md#checks-you-can-run) distinguish
standalone renderer checks from the integration suite that needs that checkout.
