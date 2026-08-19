# Config conventions

Three config formats, same discipline. Pick by who edits it:

| Format | Editor | Use when |
|---|---|---|
| YAML file | humans + agents in a text editor; shared across repos | product definitions consumed by many generators (stator lineup) |
| `PARAMS` dicts at top of macro | the agent / engineer editing the macro | single-generator knobs (plate sizes, clearances, hole patterns) |
| FreeCAD `Params` spreadsheet | someone in the FreeCAD GUI | fixtures a technician tunes without a text editor |

## YAML

```yaml
# ── Core geometry ───────────────────────────────  (units: mm, deg)
outer_diameter: 60.0          # OD at tooth tips
inner_diameter: 36.65         # bore
slot_count: 24

# ── Side wire guides (fly winder) ────────────────
# Consumed by macros/SideGuideGenerator.FCMacro.
# tip_gap: opening between the guide-wing tips. Default shoe_width + 1.0.
side_guide:
  tip_gap: 6.00
```

- Every key: unit in the section header, meaning in a trailing comment.
- Downstream generators **extend** with a namespaced block (`side_guide:`),
  never a parallel table of the same numbers elsewhere.
- Readers should be tolerant: pull the keys you need, ignore the rest.
- Writers must be **idempotent**: replace the block if present, append if not.

```python
def upsert_block(text, header, block):
    """Replace an existing '<header>...' block or append it once."""
    import re
    pat = re.compile(r"(?:%s\n)+(?:#.*\n)*[a-z_]+:\n(?:[ \t]+.*\n?)*" % re.escape(header))
    new = header + "\n" + block.rstrip("\n") + "\n"
    return pat.sub(new, text, count=1) if pat.search(text) else text.rstrip("\n") + "\n\n" + new
```
(We shipped seven configs each with the same banner ×29 because the first
version of that writer just appended. Diff the config, not only the outcome.)

## PARAMS dicts

```python
COMMON = dict(
    plate_thickness  = 4.7,    # SendCutSend .187" 5052 (no 4.0 gauge)
    cutout_clearance = 0.75,   # radial clearance around sliced profiles
    flange_hole_dia  = 6.6,    # M6 clearance
)
FLY = dict(COMMON,
    plate_len = 460.0, plate_wid = 180.0,
    unit_spacing = 180.0,      # HRP85 centre-to-centre
    pocket_style = "silhouette",
    deck_hole_xs = (-215, -70, 70, 215),
    deck_hole_zs = (30, 130),
)
```
- One dict per part; `dict(COMMON, ...)` for inheritance.
- Booleans as feature switches (`bend=True`, `side_plates=True`).
- Machine constraints as single named numbers others derive from.

## Spreadsheet (`Params`)

Created on first run from a `GLOBALS` list of `(alias, value, comment)` and a
per-SKU table with a header row; read back with `sheet.get(alias)`. Provide a
`build` selector (`ALL`, `S32`, `S32_L10`) and cheap-preview switches
(`model_threads = 0`).
