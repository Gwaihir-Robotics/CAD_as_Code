# DFM checklist — encode these as parameters/rules in the generator

## Sheet metal (laser + brake; e.g. SendCutSend)
- Use a stocked gauge (there is no 4.0 mm; 4.7 mm / .187" 5052 is).
- Bend radius ≈ thickness (we use r = T for ≤5 mm Al); bend relief at ends.
- Hole-to-bend distance ≥ ~2.5T + r; the generator should report violations.
- One part gets **round holes**, the mating part gets **slots** (adjustment
  lives in exactly one part).
- Material-outside bends: flange appended beyond the original edge; keep the
  flat pattern in mind (no round-into-corner features).
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

## Fixtures / interfaces
- One centreline height across all SKUs (`center_height`), derive the rest.
- Anti-rotation feature + single centre screw beats multiple tapped holes.
- Set-screw hubs on caps make stack length adjustable without new parts.
- Fit clearances explicit (`fit_clr`, `iface_fit`), never baked into a
  dimension.

## Interchangeability
- Left/right: flip-symmetric about a midplane, rotate 180°, prove residual 0.
- Universal side plate: add the mirrored flange rather than a second SKU.
