# Safety razor: design brief

A three-piece double-edge (DE) razor: a top cap and baseplate clamped around a
standard steel DE blade, and a handle that screws onto the cap's post.

The product is a brass or stainless steel razor made by a factory. Printed
carbon-fibre-filled parts are working prototypes for fit, form, assembly and
first shave tests. One generator and one config produce both: a printable
prototype and a production package to hand to a factory. The shave geometry is
identical in both, so what you test is what you hand over.

This is a public CAD-as-Code example. Gap and exposure on a printed head depend
on the printer and material, so measure every printed head before shaving with
it. A plastic head is also lighter and less stiff than metal, so it will not
shave exactly like the production part.

All numbers live in [config.yaml](config.yaml). This brief refers to them by
key and does not repeat them. A name such as `blade.*` or `hardware.*` means a
group of values in that file. The sources behind the reference values, and the
measurement log, are in [reference/](reference/README.md).

## Phases

1. **Printed prototypes** (`process: prototype`). Check blade and handle fit,
   assembly, the low profile around the nose, and approximate gap and exposure.
   Shave-test with care.
2. **Factory samples** (`process: production`). The factory makes a few metal
   heads from the production package. The first true shave test.
3. **Production.** After samples pass inspection.

## Scope

| Item | Status |
|---|---|
| Top cap | Designed here |
| Baseplate | Designed here, one per shave tier |
| DE blade | Reference part (`blade.*`): Dorco ST301, never altered |
| M5 × 0.8 threaded post | Production: part of the cap. Prototype: a stainless countersunk screw stands in for it (`hardware.*`) |
| Handle | Designed here, one for every tier, with a female M5 × 0.8 thread, the size most factories use for DE handles |
| M5 heat-set insert | Prototype only: a brass insert carries the handle's thread (`hardware.insert.*`). Reference part, never altered |

## Frame

- Origin at the centre of the blade's centre hole.
- X along the blade length, Y across its width, Z up toward the top cap, along
  the post axis.
- The blade's flat centre section lies in the plane Z = 0. The two halves bend
  down symmetrically toward the cutting edges at ±Y.
- The handle hangs below the baseplate along −Z, on the post axis. Its top face
  sits on the baseplate's handle seat.

## Definitions

These set how each check measures. Treat them as part of the requirements.

- **Cutting angle** (`shave.bend_angle`): angle of the bent blade section below
  the horizontal XY plane.
- **Shave plane**: on each side, the line in the YZ section tangent to the top
  cap's outer edge and the safety bar's outer apex.
- **Blade gap** (`shave.tiers.*.gap`): shortest distance from the sharpened edge
  to the safety bar.
- **Blade exposure** (`shave.tiers.*.exposure`): signed distance from the
  sharpened edge to the shave plane, measured perpendicular to the plane. Zero
  is neutral, negative sits behind the plane, positive protrudes past it.
- **Blade reveal**: how far the blade extends beyond the top cap's outer edge,
  seen from above. Reported, not limited. A large reveal does not mean an
  aggressive head; the shave plane decides how the edge meets skin.
- **Clamp distance**: distance from the cutting edge to the last line where
  both the top cap and the baseplate touch the blade. The check measures it at
  the ribs between drain slots. Under a slot the baseplate's support ends
  further from the edge; the generator reports that distance (open question 7).
- **Head height** (`head.max_height`): distance along the post axis from the
  handle-seat face of the baseplate to the highest point of the top cap. The
  safety bars hang below the seat face, so the head is taller overall; the
  generator reports the overall height (open question 15).
- **Thread engagement** (`handle.min_engagement`): length of the post or screw
  inside the handle's thread, the insert in the prototype or the tapped hole in
  production, with the head assembled and the handle tight against the seat.
- **Tip clearance** (`handle.tip_clearance`): distance from the end of the post
  or screw to the bottom of the handle's hole.

## Shave tiers

Blade gap and exposure set together how mild or aggressive a head shaves, so
the config sets them as pairs, called tiers (`shave.tiers`). Published labels
disagree. One guide puts mild gaps up to about 0.60 mm, medium at 0.60–0.70 mm
and aggressive above 0.70 mm ([Sharpologist, 2024][head-design]), and the same
commercial razor is called mild in one review and medium-aggressive in others
([Sharpologist, 2023][prismatic]). No source we found publishes measured
exposure ranges.

So the tier names here are relative to each other, and their values are
starting targets. Measurements of printed heads, then factory samples, replace
them. The example builds three tiers. All three share one top cap; only the
baseplate changes. Print the mildest first: printed exposure misses its target
by an unknown amount, and an error toward positive makes a mild head shave like
a more aggressive one.

## Reference blade

Dorco ST301 (Platinum Extra). Not the STP301 "Prime", which is thinner. Blades
differ between brands by up to about 0.3 mm in width ([B&B blade
dimensions][bnb]), enough to move the edge more than one tier step, so the
whole test series uses this one blade. The `blade.*` values will come from
measuring several ST301 blades with calipers. Until `blade.source` is filled
in, they are nominal values and estimates.

The blade's centre cutout is a keyhole pattern, the same on most DE blades: a
round centre hole, a narrow slot running the length of the cutout, and wider
ovals and diamonds along it. The narrow slot is the only part with parallel
sides, so the alignment bars run in it. Any DE blade fits any DE razor, so the
bars are sized to pass through the narrowest and shortest cutout we have a
figure for (`blade.any_blade`), not through this blade alone. A blade with a
wider slot has play, and its slot width (`blade.neck_width`) sets how much. The
reference picture for the pattern is the illustration in [Sharpologist's
article on blade compatibility][universal]. The config's cutout values were
traced from that illustration and from a second drawing. Neither is to scale
and neither names the ST301, so every cutout value stays provisional until a
caliper reading replaces it ([sources and traced values](reference/de-blade-drawing.md)).

The centre hole needs no measurement. Razors with an M5 post are common and
take any DE blade, so the hole clears a 5 mm post. The design uses the hole
only for this clearance. The width of the blade's flat centre section has its
own key (`head.flat_width`), so a blade measurement cannot change the shape of
the head.

## Reference razor

A slim commercial three-piece head the author finds mild: about 6 mm from the
bottom of the baseplate to the top of the cap, 5 mm at the thickest section with
a blade installed, and about 2.5 mm of reveal. It sets the height target and
shows that a large reveal can still shave mildly.

## Hard requirements

The generator checks each of these, for every tier and both processes, and
prints `RESULT FAIL` if any one misses. The handle and insert rows are planned:
the generator does not build the handle yet.

| Requirement | Config key | Reason |
|---|---|---|
| Blade gap equals the target within CAD precision | `shave.tiers.*.gap` | Sets how aggressive the shave is |
| Exposure equals the target within CAD precision | `shave.tiers.*.exposure` | Too much exposure cuts skin |
| Cutting angle equals the target | `shave.bend_angle` | Blade geometry depends on it |
| Shave geometry is identical in both processes | `process` | The prototype must test the product |
| Top cap is identical for every tier | `shave.tiers` | Each test then changes only the baseplate |
| Clamp distance at most the limit | `fit.clamp_max` | An unsupported edge chatters |
| Head height at most the limit | `head.max_height` | A low head reaches under the nose |
| Head covers the blade envelope, or end notches expose the tabs | `head.length`, `blade.envelope_length` | Blade ends stay covered or deliberately reachable |
| Alignment bars sit fully inside the modelled blade's cutout, clear of the centre hole and the cutout ends | `bars.*`, `blade.neck_width`, `blade.cutout` | Bars locate the blade, not the post |
| Bars pass through any DE blade: at least the minimum play in the narrowest known slot, and no bar reaches past the shortest known cutout | `bars.width`, `bars.min_play`, `blade.any_blade` | Any DE blade fits the head |
| Pocket size equals bar size plus clearance on each side | `process_limits.*.part_clearance` | Cap and baseplate assemble without binding |
| Named walls at least the minimum for the process | `process_limits.*.min_wall` | Thinner walls crack, print poorly or cannot be made |
| Thread engagement at least the minimum | `handle.min_engagement` | A short engagement strips the thread |
| Tip clearance at least the minimum | `handle.tip_clearance` | A post that bottoms out stops the handle before it clamps the head |
| Insert hole equals the insert maker's diameter and depth, plus the printer's hole allowance | `hardware.insert.*` | Too small cracks the handle; too large leaves the insert loose |
| Wall around the handle's hole at least the insert maker's minimum, also under the grip grooves | `hardware.insert.min_wall` | Hot brass pushes thin plastic out of shape |
| Handle's top face fits inside the flat of the baseplate's handle seat | `handle.top_dia`, `baseplate.handle_seat_dia` | The baseplate slopes down outside the seat flat, so a wider handle rests on the slopes and rocks |
| Each part is one watertight, valid solid | | Printable, machinable and exportable |
| STEP and mesh read back with matching volume | | Exports match the model |

The generator checks walls as named distances: pocket to edge, bore to pocket,
drainage slot to edge, post or countersink to bar, handle hole to grip groove.

## Design choices

- **One top cap, one baseplate per tier.** With the cap and blade fixed, the
  safety bar's position sets both values: moving it in or out changes the gap,
  and moving it up or down moves the shave plane, which changes exposure.
- **Integral post in production, screw in the prototype.** A metal cap carries
  its M5 × 0.8 post as part of the cap, machined or cast with it, and the
  drawing calls out the thread. The thread is not modelled. A printed thread
  this fine is weak in plastic, so the prototype cap has a countersink instead,
  and a stainless countersunk screw passes down through cap, blade and
  baseplate into the handle. Tighten it snug, not hard: plastic creeps under
  steady load.
- **Raised alignment bars that fit any blade.** Two narrow bars on the cap
  underside run in the blade's narrow slot, one each side of the centre hole,
  and locate the blade. The post does not. The bars are narrower than the
  narrowest slot we know of, so any DE blade fits. The cost is play: the blade
  can slide around the bend by up to half the difference between slot and bar,
  which moves one edge out and the other in. A little play is normal on DE
  razors, so the head accepts it. The generator reports gap, exposure and clamp
  distance with the blade slid fully each way. Measure both sides of every
  assembled head.
- **Centre the blade for tier tests.** At the modelled slot, play moves
  exposure by about as much as one tier step. To compare tiers, assemble with
  the screw loose, set a feeler gauge of the tier's gap between the edge and
  the safety bar on each side, nudge the blade until both fit snugly, then
  tighten. For everyday shaving, skip it.
- **Shavers can loosen the handle.** Some shavers back the handle off a little
  for a more aggressive shave: the clamp relaxes, the blade's bend opens, and
  gap and exposure grow. The generator models a fully clamped blade only, so
  every check assumes a snug screw.
- **Bars keep their width in every process.** The blade fit does not change with
  the process. If first-layer squish makes printed bars too wide, sand their
  sides.
- **Pockets derive from bars.** Pocket size is bar size plus the process's part
  clearance per side, so changing the process changes only the pockets.
- **Closed comb guard.** A solid safety bar with drainage slots behind it.
- **Prototype material.** Carbon-fibre-filled PETG or PET: stiff, stable, and
  tolerant of water and warmth. Not PLA-CF, which softens near hot-tap
  temperature. Needs a hardened nozzle. Sand the skin-contact surfaces (cap edge
  and safety bar) after printing.
- **Medium classic handle.** A straight round handle about 90 mm long and 12 mm
  across, with grip grooves and a slightly wider end cap, a common size for
  three-piece razors. One handle serves every tier. The seat flat is 11 mm
  wide today, so a 12 mm handle does not fit it (open question 13).
- **Brass heat-set insert in the prototype handle.** You unscrew the handle at
  each blade change, and a printed M5 × 0.8 thread wears out fast. A brass
  insert pressed in with a soldering iron gives a metal thread. The handle has a
  straight blind hole at the top, sized from the insert maker's drawing and
  about 1 mm deeper than the insert, with no chamfer ([CNC Kitchen][inserts]).
  Printed holes come out slightly small, so the prototype adds a per-printer
  allowance (`hardware.insert.hole_allowance`). The production handle is
  turned and tapped M5 × 0.8 directly.
- **Handle prints upright.** Printed with the insert end up, the hole comes out
  round. A brim keeps the tall, narrow part stuck to the bed.
- **Handle weight.** A printed handle is light. A solid brass handle this size
  is heavy, so the production handle may need a bore or a smaller diameter. The
  generator reports the mass in each material.
- **Fillets are cosmetic on prints.** Edge breaks on skin-contact edges are
  modelled at nominal size; at FDM nozzle widths they print roughly, and the
  factory makes them properly.

## Outputs

Each run writes `output/<family>/<tier>/rNNN/` (regenerable, not committed).
With `EXPORT_DIR=exports`, a passing build is also copied to `exports/`.

| Process | Outputs |
|---|---|
| `prototype` | Per part: FreeCAD model, STEP, and a 3MF oriented for printing |
| `production` | Per part: FreeCAD model, STEP, and a drawing (DXF) with the dimensions the factory must hold; an inspection list taken from the hard requirements; material, finish and thread callouts |
| both | A report (Markdown) with the check table and 2D drawings (SVG): a cross-section of the assembled head, a detail of the blade edge with the shave geometry labelled, the blade with the bars in its cutout, the top cap from below, the baseplate from above, and a section of the handle with the insert or thread |

## Verification summary

After building, the generator prints the target and measured value for blade
gap, exposure, cutting angle, clamp distance, reveal, head height, bar width,
pocket width, each named wall, thread engagement, tip clearance and the insert
hole, then `RESULT PASS` or `RESULT FAIL`. On a
printed head, check gap and exposure with feeler gauges and calipers. The same
list becomes the factory's inspection plan.

## Open questions

Suggested defaults are in `config.yaml`, each marked `OPEN`.

1. **Blade measurements.** Measure several Dorco ST301 blades: the narrow-slot
   width first, since it sets how far the blade can slide, then width, length,
   cutout length and thickness. The centre hole only has to clear the M5 post. The ovals and diamonds only need
   to be wider than the bars.
2. **Bar length and position** (`bars.*`). Each bar must pass through any DE
   blade's cutout (`blade.any_blade`), clear of the centre hole. The
   narrowest and shortest figures come from an unsourced spec; a blade that
   breaks them changes `blade.any_blade`.
3. **Bend radius** (`head.bend_radius`). Set it, or let the generator derive it
   from the cutting angle and clamp distance. No bend radius reaches
   `head.depth_range`: even a sharp bend leaves the blade edges 19.5 mm apart,
   and the safety bars add about 1 mm on each side. Widen the range or remove
   it. The current build is 22.7 mm deep.
4. **Safety bar profile** (`guard.profile`): straight, scalloped, or a slotted
   bar as on some older designs.
5. **Prototype screw** (`hardware.screw_head_*`). Take the countersunk head
   diameter and height from the datasheet of the screw you buy. Choose the
   length too: the head is 6 mm tall, so a 12 mm screw leaves 6 mm of thread in
   the handle.
6. **End notches** (`head.end_notches`): full cover, or notches for gripping
   the blade tabs.
7. **Clamp limit** (`fit.clamp_max`). Two results conflict with it. Under each
   drain slot the baseplate's support ends about 2.06 mm from the edge, past
   the limit, because the slot's minimum width (`baseplate.drain_slot_min_width`)
   cuts into the support. The top cap still presses the blade at the limit
   along its whole length. Decide between narrower slots, a separate limit for
   the support under a slot, or the current build. The reference razor also
   shows about 2.5 mm of blade, so its cap clamps at least that far from the
   edge and it would fail this limit, yet it shaves mildly. The limit may be
   tighter than it needs to be.
8. **Production material and method** (`material.*`): brass or stainless,
   machined or cast. The factory may advise. Casting needs draft angles;
   machining needs tool access and inside-corner radii.
9. **Production limits** (`process_limits.production.*`): clearance and minimum
   wall from the factory.
10. **Prototype filament** (`material.prototype`): PETG-CF or PET-CF.
11. **Drawing format.** DXF export works from a script; PDF export needs
    FreeCAD's GUI and is not yet tested.
12. **Heat-set insert** (`hardware.insert.*`). The defaults come from the
    ruthex RX-M5x9.5 drawing ([3DJake listing][ruthex]); CNC Kitchen's
    TC-M5x9.5 has the same length. Check the drawing for the insert you buy,
    then print a test hole and set `hardware.insert.hole_allowance` so the
    insert pre-seats with a little resistance.
13. **Handle shape** (`handle.*`): length, diameter, grip pattern (grooves or
    knurling) and end cap. Production could knurl on a lathe instead of
    cutting grooves. Settle the top diameter against the seat flat
    (`baseplate.handle_seat_dia`): widen the seat, or neck the handle in at the
    top.
14. **Production handle mass** (`handle.*`): solid, bored, or slimmer, once the
    generator reports the mass.
15. **Head height datum** (`head.max_height`). The limit is measured from the
    handle seat. The safety bars hang about 1.8 mm below the seat on the mild
    tier and more on the others, so the head is about 7.8 mm tall overall, and
    the reference razor measures about 6 mm from the bottom of its baseplate.
    Decide which height reaches under the nose, and limit that one. The cap
    crown is as thick as the prototype screw's head, so a lower head needs a
    thinner screw head or a different fastener.
16. **Print orientation.** The 3MF files lay the cap crown-down and the
    baseplate as modelled. Neither part has a flat face to print on, so both
    need supports, and the curved blade seats print as layer steps. Standing
    each part on end prints the whole cross-section, including the blade seat
    and the safety bar, in the printer's most accurate plane. It needs a brim,
    and a small support under each bar. Test both.

[head-design]: https://sharpologist.com/the-art-and-science-of-safety-razor-head-design/
[prismatic]: https://sharpologist.com/prismatic-tribute-80-years-making/
[universal]: https://sharpologist.com/are-safety-razor-blades-universal/
[bnb]: https://www.badgerandblade.com/forum/wiki/Comprehensive_Double-Edge_DE_Razor_Blade_Data_Table
[inserts]: https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts
[ruthex]: https://www.3djake.com/ruthex/threaded-inserts-m5-50-pieces
