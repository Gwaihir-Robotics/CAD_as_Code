# Reference material

This folder holds the outside information the design depends on: where each
bought part's dimensions came from, and the measurements that replace the
estimates. The brief says what the design must do, the config holds the
numbers, and this folder shows where the reference numbers came from.

In the brief, a name such as `blade.*` or `hardware.*` points to a group of
values in [config.yaml](../config.yaml). It is a config key, and no file has
this name. The table below links each group to its source.

## Sources

| Config keys | Source | Status |
|---|---|---|
| `blade.width`, `blade.length`, `blade.envelope_length`, `blade.slot_length` | [Badger & Blade blade data table][bnb]. Across brands it gives widths of 21.89 to 22.18 mm, lengths of 42.72 to 43.04 mm and cutout lengths of 35.98 to 36.15 mm | Ranges across brands. Dorco ST301 caliper readings still needed |
| `blade.thickness` | Forum reports of about 0.10 mm for the ST300 and ST301 | Unconfirmed |
| `blade.hole_dia`, `blade.neck_width`, `blade.cutout` | Traced from a dimensioned drawing in an eBay listing for DE blades ([notes and traced values](de-blade-drawing.md)). The drawing is not to scale, does not name the ST301, and is not stored here | Provisional |
| `blade.edge_span`, and a second source for `blade.length`, `blade.width` and `blade.thickness` | Printed on [the same drawing](de-blade-drawing.md): 37.0, 42.7, 22.0 and 0.1 mm | Nominal values from an eBay listing, maker unknown |
| Cross-check for the cutout values | Illustration in [Sharpologist: Are safety razor blades universal?][universal], traced the same way ([results](de-blade-drawing.md)). Linked, not copied | Agrees within about 0.4 mm; not to scale |
| `blade.any_blade` | A spec with no named source: narrow slot 2.10 mm, round holes 5.35 mm at ±10.025 mm | Unsourced. Replace it if you find a narrower or shorter cutout |
| `hardware.screw_head_dia`, `hardware.screw_head_height` | DIN 7991 nominal sizes for M5: head 10.00 mm across, 2.80 mm high | Generator default. Use the datasheet of the screw you buy |
| `hardware.post_thread`, `hardware.handle_thread` | M5 × 0.8, the thread most DE handle makers use | Fixed |
| `hardware.insert.*` (planned, with the handle) | [ruthex RX-M5x9.5 drawing][ruthex]: 6.4 mm hole, 7.1 mm outside, at least 2.6 mm of wall. Install method from the [CNC Kitchen guide][inserts] | Check the drawing of the insert you buy |
| `shave.tiers` | Gap ranges from [Sharpologist, 2024][head-design]. No source we found publishes measured exposure | Starting targets. Printed-head measurements replace them |
| `head.max_height` | A slim commercial three-piece head the author measured: about 6 mm tall, 5 mm at its thickest with a blade, about 2.5 mm of blade showing | One razor, measured by hand |

## Adding files

Put the source itself here when you have it and its licence lets you share it:
a datasheet PDF, a vendor's STEP file, a photo of a caliper reading. Name the
file after the part, such as `dorco-st301-blade.jpg`, and add a row above. This
repository is public, so link to a copyrighted drawing or table and do not copy
it in.

## Measurements

Record caliper readings in [measurements.md](measurements.md). When a reading
replaces a config value, change the value's comment in `config.yaml` from
`OPEN` to the source, for example `measured, 5 blades, caliper 0.01 mm`.

[universal]: https://sharpologist.com/are-safety-razor-blades-universal/
[bnb]: https://www.badgerandblade.com/forum/wiki/Comprehensive_Double-Edge_DE_Razor_Blade_Data_Table
[head-design]: https://sharpologist.com/the-art-and-science-of-safety-razor-head-design/
[ruthex]: https://www.3djake.com/ruthex/threaded-inserts-m5-50-pieces
[inserts]: https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts
