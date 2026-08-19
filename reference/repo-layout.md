# Repo layout

One project = one git repo (or one top-level folder in a mono-repo) laid out so
that *source* and *artifact* are never confused:

```
<project>/
  macros/            *.FCMacro generators — the source of truth
  docs/              design notes, DFM decisions, commercial references, img/
  external_imports/  vendor STEP/DXF (HRP85, linear axes, rails) — never edited
  generated/         what the macros write: FCStd, STEP, DXF, SVG — never hand-edited
  exports/           vendor bundles (e.g. SendCutSend zip; qty in filenames)
  tools/             non-geometry helpers (render_views.FCMacro, exporters)
  README.md          one-line regenerate command per macro
  .gitignore         *.FCStd1  *.FCBak  .DS_Store  *.FCStd.*
```

Rules
- `generated/` is disposable. Wrong output ⇒ fix macro/config, re-run.
- Commit outputs anyway (STEP at least) so collaborators without FreeCAD can
  open them and STEP diffs act as a regression signal.
- Macros resolve paths relative to their own file
  (`PROJECT_DIR = dirname(dirname(abspath(__file__)))`), never the CWD.
- Vendor STEPs live in `external_imports/` with a README naming the source
  URL/part number and any measured facts.
- Shared product configs (e.g. stator YAMLs) live in *their* repo; generators
  read them by path and add namespaced keys when they need more.
- Version generators by content, not filename, once stable — `_v4` suffixes are
  fine during exploration; retire old ones into `archive/` when superseded.
