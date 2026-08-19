# CAD as Code

**Git-backed, parametric CAD with a coding agent.** A Claude Code skill plus the
reference material behind Gwaihir Robotics' way of building fixtures, jigs and
machine plates: FreeCAD generator macros driven by config (YAML / PARAMS /
spreadsheet), run headless, verified by scripted checks, outputs regenerable —
config-as-code borrowed from Kubernetes and applied to CAD.

Read the long-form write-up: [`blog/cad-as-config.md`](blog/cad-as-config.md)
(also published at gwaihirrobotics.com/blog/2026-08-cad-as-config).

## The honest premise

You cannot ask an agent for "a CAD model of an airliner." What works is
decomposing to parts, pinning frames and datums, feeding vendor geometry as
ground truth, and asking the agent for a **generator** plus the **checks** that
prove it — then iterating on screenshots and committing config, generator and
outputs together. Details in [`SKILL.md`](SKILL.md).

## Install the skill

```sh
git clone git@github.com:Gwaihir-Robotics/CAD_as_Code.git ~/code/CAD_as_Code
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
  dfm-checklist.md          sheet metal, casting, machined, fixtures, interchangeability
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
