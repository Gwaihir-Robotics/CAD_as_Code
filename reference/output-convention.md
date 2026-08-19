# Output convention: `output/<family>/<SKU>/<rev>/` + manifest

Generated geometry is an **artifact**, so treat it like a build artifact:
addressable by what produced it, reproducible from config, and mostly not
committed.

```
output/
  <family>/                 one generator family: frameless-kit, rotor-housings, fly-plates
    <SKU-or-id>/            S32 … S100, drone-6010, or a single-variant "default"
      r001/                 revision folder — bump when config or generator changes
        cad-manifest.json   provenance + resolved parameters (below)
        <id>.FCStd          the document
        step/
          <id>-<part>.step  one STEP per part, family+SKU prefix in the name
        <id>-<part>.dxf     flat patterns, if any
        renders/            PNGs from the render macro, if any
exports/                    CURATED, COMMITTED: vendor bundles + latest STEP per part
```

## Naming
- `<id>` = `<family>-<SKU>` or the product id (`drone-6010`); every file inside
  starts with it so files stay meaningful when copied out of the folder.
- Part suffixes are stable snake_case (`rotor_can`, `stator_mount`,
  `side_plate`); quantities only in `exports/` filenames (`…_x2.step`).
- Revision `rNNN` is allocated by the generator: reuse the folder when the
  manifest's `config_sha` matches, otherwise create the next `rNNN`.

## cad-manifest.json
```json
{
  "format": "cad-manifest", "schemaVersion": 1,
  "design": "arbor-S60@3f9a1c2b7d10",       // <id>@<config_sha[:12]>
  "generator": "generator_template.FCMacro@8a1f…",   // sha of the macro source
  "units": "mm",
  "config_path": "configs/stator_60mm_24n.yaml",
  "params": { "arbor_od": 36.61, "stack_length": 20.0 },   // resolved values actually used
  "parts": { "arbor": { "file": "step/arbor-S60-arbor.step", "volume_mm3": 27871 } },
  "checks": { "hole_residual": 0.0, "step_roundtrip_dV": 0.0, "result": "PASS" },
  "generated_at": "2026-08-19T03:31:02Z"
}
```
Same config + same generator ⇒ same `design` string ⇒ same geometry. That is
the reproducibility contract; it is what lets `output/` be gitignored.

## Git policy (hybrid)
- `.gitignore`: `output/` (everything), `*.FCStd1`, `*.FCBak`.
- Commit `exports/`: what a human without FreeCAD needs — vendor bundles,
  the latest STEP per part, the manifest that produced them. Refresh by
  copying from the current `rNNN` (a `tools/export.sh` or the generator's
  `--export` switch), never by hand-editing.
- Commit `configs/` and `macros/` always; a PR's real diff is there.
- If a collaborator must see history of geometry, diff the STEP in
  `exports/` or re-generate the old rev from the old config commit.

## Template support
`templates/generator_template.FCMacro` implements all of this: rev allocation
by `config_sha`, `<id>-<part>.step` naming, manifest with resolved params and
check results, optional `EXPORT_DIR` copy of the latest STEPs.
