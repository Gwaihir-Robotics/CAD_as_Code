# Measurements

No readings yet. Fill in a table when you measure, then update `config.yaml`.

## Dorco ST301 blade

Caliper resolution: [0.01 mm]. Measure on the blade's body and tabs, never
across the sharp edges. Measure the narrow slot first, because it sets how far
the blade can slide.

| Dimension | Config key | Blade 1 | Blade 2 | Blade 3 | Blade 4 | Blade 5 | Mean |
|---|---|---|---|---|---|---|---|
| Narrow slot width | `blade.neck_width` | | | | | | |
| Centre hole diameter | `blade.hole_dia` | | | | | | |
| Width, edge to edge | `blade.width` | | | | | | |
| Length | `blade.length` | | | | | | |
| Cutout length, end to end | `blade.slot_length` | | | | | | |
| Thickness | `blade.thickness` | | | | | | |

## Prototype screw

| Dimension | Config key | Datasheet | Measured |
|---|---|---|---|
| Head diameter | `hardware.screw_head_dia` | | |
| Head height | `hardware.screw_head_height` | | |

## Printed heads

One row per printed head and side. Centre the blade before measuring (README,
step 7).

| Date | Tier | Filament | Side | Gap target | Gap measured | Exposure target | Exposure measured | Notes |
|---|---|---|---|---|---|---|---|---|
