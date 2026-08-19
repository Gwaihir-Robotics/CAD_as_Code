# Example: stator YAML → winding arbor

Three trimmed stator configs (`configs/`) and a minimal generator that turns
one of them into a winding arbor (`arbor_from_stator.FCMacro`, a thin wrapper
around `templates/generator_template.FCMacro`).

```sh
FC=/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
CONFIG=configs/stator_60mm_24n.yaml OUT_DIR=generated $FC arbor_from_stator.FCMacro
```

Expected tail of the output:
```
Arbor_S60_L20:
  hole residual        0.0000 mm^3
  arbor OD             36.610 (bore 36.65 - clr)
  ...
RESULT PASS -> generated
```

Our production versions of this idea (riser + arbor family for every SKU and
stack length, real divot clocking, DXF overlay, spreadsheet params; the wire
guides; the coating jig) are internal, but the blog post in `../../blog/`
walks through all four in detail.
