# DE blade cutout: sources and traced values

The picture to look at is the illustration in Sharpologist's article
[Are safety razor blades universal?][universal]. It shows the keyhole cutout
clearly, and this folder links to it and does not copy it.

The cutout values in the config were first traced from a different picture: a
dimensioned drawing from an eBay listing for DE blades, which the author supplied
during the design review (2026-11-18). It has Japanese labels and no maker's
name, it does not name the Dorco ST301, and the listing's link was not kept.
The Sharpologist illustration was traced afterwards as a cross-check (last
section), and the two agree.

## What the eBay drawing gives directly

| Dimension | Value (mm) | Config key |
|---|---|---|
| Length | 42.7 | `blade.length` |
| Length of the cutting edge | 37.0 | `blade.edge_span` |
| Width | 22.0 | `blade.width` |
| Thickness | 0.1 | `blade.thickness` |

## What Claude traced from the eBay drawing

The drawing shows the keyhole cutout but gives no dimensions for it. Claude
measured the cutout from the image's pixels and scaled it with the printed
dimensions. The drawing is not to scale: the blade body is drawn about 10% too
long for its width, so the widths come out as ranges. Lengths along the blade
look reliable, because the traced cutout length (35.96 mm) matches the 36.0 mm
from the Badger & Blade table.

| Feature | Distance from centre (mm) | Width across the blade (mm) |
|---|---|---|
| Centre hole | 0 to 2.4 | 5.3 to 5.9 diameter |
| Narrow slot | 2.5 to 7.4 | 2.2 to 2.4 |
| Oval | 7.5 to 9.2 | 6.6 to 7.3 |
| Narrow slot | 9.3 to 10.2 | 2.2 to 2.4 |
| Diamond | 10.3 to 15.3, widest at 12.7 | 6.5 to 7.1 |
| Narrow slot | 15.4 to 16.1 | 2.2 to 2.4 |
| End oval | 16.2 to 17.9 | 6.6 to 7.3 |

These became `blade.hole_dia`, `blade.neck_width` and `blade.cutout` in the
config, all marked `OPEN`. A caliper reading across the narrow slot of a Dorco
ST301 replaces the least certain and most important one.

## Cross-check: the Sharpologist illustration

Sharpologist's article [Are safety razor blades universal?][universal] has an
[illustration of a DE blade][universal-image] labelled 23 mm wide, 37 mm along the edge and 43 mm
overall. 

Claude traced its cutout the same way. The illustration is not to scale either:
no single scale fits its three labelled dimensions. Scaled so the blade body is
37 mm long, it gives:

| Feature | This drawing (config value) | Sharpologist illustration |
|---|---|---|
| Cutout length | 36.0 | 35.8 |
| Narrow slot width | 2.2 to 2.4 (2.40) | 2.2 |
| Centre hole diameter | 5.3 to 5.9 (5.80) | 5.0 |
| Oval centre, from blade centre | 8.35 | 8.7 |
| Diamond centre | 12.8 | 12.9 |
| End oval centre | 17.1 | 16.9 |

The two sources agree on the pattern, on the feature positions to within about
0.4 mm, and on a narrow slot of roughly 2.2 to 2.4 mm. Neither replaces a
caliper reading. The illustration's 23 mm width is a rounded figure (0.9 in);
measured blades are 21.89 to 22.18 mm wide.

[universal]: https://sharpologist.com/are-safety-razor-blades-universal/
[universal-image]: https://sharpologist.com/wp-content/uploads/2025/03/de-blade-dimensions-1-720x720.jpeg
