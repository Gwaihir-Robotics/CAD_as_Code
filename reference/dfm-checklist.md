# DFM checklist — encode these as parameters/rules in the generator

## Sheet metal (laser + brake; e.g. SendCutSend)
- Use a stocked gauge (there is no 4.0 mm; 4.7 mm / .187" 5052 is).
- Bend radius ≈ thickness (we use r = T for ≤5 mm Al); bend relief at ends.
- Hole-to-bend distance ≥ ~2.5T + r; the generator should report violations.
- One part gets **round holes**, the mating part gets **slots** (adjustment
  lives in exactly one part).
- Material-outside bends: flange appended beyond the original edge; keep the
  flat pattern in mind (no round-into-corner features).
- **Min hole ⌀ / slot width ≥ T** (laser cannot form a feature narrower
  than the plate is thick); the generator should report violations.
- Kerf taper 0.5–2° on thick plate — a cut edge is not square. Never use one
  as a bearing, flank, or press-fit surface.
- Quantity in the export filename (`Part_4.7mm-5052_x2.step`).

## Casting / MJF / resin
- Ø5.0 minimum through-hole (Ø4.5 in metal casting is a tap-drill, not a hole).
- No 90° internal dihedrals; add draft or a 45° wedge where fillets fail.
- Wall ≥ 2.5 mm; avoid thin crescents from off-centre flats.
- Machined-after-cast features (rail seats, bores) called out separately.

## Machined (lathe/mill/Swiss)
- Design to bar stock: lip Ø just under the as-bar diameter (allow undersize
  tolerance), body one clean skim.
- Prefer one part number ×N over N part numbers ×1 (coupler shared across rod
  sizes; arms identical both ends).
- Aspect ratio: long thin rods are expensive; consider rails/carriages instead.

## Gears / reduction stages
- **Never laser- or waterjet-cut involute teeth.** Tooth space at our modules
  (m≈0.7 → ~1.1 mm) is far below plate thickness — min-feature blocker, not a
  tolerance trade-off. Kerf taper also makes the flank conical: line contact
  becomes edge contact, and a profile tolerance never shows it.
- **No quench-and-tempered abrasion plate (AR400/AR500) on a load-bearing
  flank.** The laser HAZ leaves untempered martensite exactly where the
  Hertzian contact is. Use 4140 PHT or 4130-then-nitride for flat gear stock.
- **Buy the precision, make the flat parts.** Purchased: bearings, dowel and
  needle pins, and the gearset itself (a 9:1 in 81 mm is a commodity).
  Fabricated flat: carriers, output flanges, spacers, housing rings.
- **Locate on reamed/bored holes, never on a cut contour.** One drill-ream or
  bore op per flat part, datumed off a generously-toleranced cut edge.
- Budget ±0.005" contour honestly: ≈±11% of a m=0.7 tooth, ≈ 26 arcmin
  output backlash, and planet load-sharing lost unless the sun or ring floats.
- **Cycloidal is the flat-stock-friendly architecture** — multi-mm lobes, load
  shared across many pins, ratio in one stage. Tune the mesh with ground dowel
  diameter (0.0002" steps), not by re-cutting; stack 2–3 thin discs and phase
  them rather than cutting one thick one.
- **Design flat parts fineblank-ready** (uniform thickness, no post-machining):
  that is the volume path, ±0.0005–0.002" for $8–40k of tooling.
- A vendor tolerance with no Cpk, FAI, or material cert means *we* own incoming
  inspection — a cost that scales linearly with volume.

Full worked analysis (numbers, process-vs-volume ladder, material table):
`actuators/motor-pipeline/docs/gearbox-manufacturing-scalability.md`.

## Fixtures / interfaces
- One centreline height across all SKUs (`center_height`), derive the rest.
- Anti-rotation feature + single centre screw beats multiple tapped holes.
- Set-screw hubs on caps make stack length adjustable without new parts.
- Fit clearances explicit (`fit_clr`, `iface_fit`), never baked into a
  dimension.

## Interchangeability
- Left/right: flip-symmetric about a midplane, rotate 180°, prove residual 0.
- Universal side plate: add the mirrored flange rather than a second SKU.
