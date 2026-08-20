# OCC / FreeCAD workarounds we paid for

All of these came out of production generators (machine plates, wire guides,
coating jigs). Copy, don't rediscover.

## 1. Silhouette from a vendor STEP: slice, flatten, fuse
Slices at different Z produce disjoint stacked faces that won't fuse. Translate
every slice onto one plane first, fuse, keep outer wires only.
```python
def band_silhouette(shape, z0, z1, n=5):
    faces = []
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        for sol in shape.Solids:
            for w in sol.slice(Vector(0, 0, 1), z):
                try:
                    f = Part.Face(w); f.translate(Vector(0, 0, z0 - z)); faces.append(f)
                except Exception: pass
    fused = faces[0]
    for f in faces[1:]: fused = fused.fuse(f)
    fused = fused.removeSplitter()
    outer = [Part.Face(f.OuterWire) for f in fused.Faces]     # fill holes
    fused = outer[0]
    for f in outer[1:]: fused = fused.fuse(f)
    return [Part.Face(f.OuterWire) for f in fused.removeSplitter().Faces]
```

## 2. `makeOffset2D` returns null / wrong / lazy OffsetCurve edges
Try join styles (2 then 0), validate `Area` grew, else fall back to a 3D
`makeOffsetShape` on an extrusion and re-slice; then rebuild edges as true
arcs/lines so STEP export doesn't mangle `OffsetCurve` wrappers.
```python
def to_analytic(face):
    edges = []
    for e in face.Edges:
        if type(e.Curve).__name__ in ("Line", "Circle"): edges.append(e); continue
        p0, pm, p1 = e.valueAt(e.FirstParameter), e.valueAt((e.FirstParameter+e.LastParameter)/2), e.valueAt(e.LastParameter)
        try: edges.append(Part.Arc(p0, pm, p1).toShape())
        except Exception: edges.append(Part.makeLine(p0, p1))
    return Part.Face(Part.Wire(Part.__sortEdges__(edges)))
```
For hairline steps left by fused slices: `smooth_face` — discretise the outer
wire (`Deflection=0.05`) and rebuild as one closed B-spline.

## 3. Slots: build the stadium as one wire
Fusing two cylinders + a box leaves a degenerate seam. Two lines + two arcs:
```python
def slot_cutter(p1, p2, dia, z0, h):
    r = dia/2; d = (p2 - p1); d.normalize(); n = Vector(-d.y, d.x, 0)
    a1, a2, a3, a4 = p1 + n*r, p2 + n*r, p2 - n*r, p1 - n*r
    face = Part.Face(Part.Wire([Part.makeLine(a1, a2), Part.Arc(a2, p2 + d*r, a3).toShape(),
                                Part.makeLine(a3, a4), Part.Arc(a4, p1 - d*r, a1).toShape()]))
    face.translate(Vector(0, 0, z0 - face.BoundBox.ZMin)); return face.extrude(Vector(0, 0, h))
```

## 4. Fuse all cutters, then cut once
Holes that graze a cutout leave razor slivers if cut one by one. Fuse the
cutters (`tool = tool.fuse(c)`), `removeSplitter()`, single `plate.cut(tool)`.
Detect grazing with `wire.distToShape(Part.Vertex(p))[0] < r + 0.3` and slot
the hole into the cutout instead (or change the hole size — tapped Ø5 instead
of Ø6.6 clearance solved it for us).

## 5. `removeSplitter` demotes to a shell
```python
def cleaned_solid(shape):
    c = shape.removeSplitter()
    if c.Solids: return max(c.Solids, key=lambda s: s.Volume)   # bare solid, not compound
    if not c.Shells: return shape
    try:
        s = Part.makeSolid(c.Shells[0]); return s if s.isValid() else shape
    except Exception: return shape
```

## 6. Multi-solid vendor STEP scrambled after placement
Each solid carries its own Placement. Compose:
`feat.Placement = pose.multiply(feat.Placement)` — never assign `pose` directly.

## 7. Fillets failing on cast/organic parts
Chain fillets fail on tangent/short edges. Fall back to a 45° chamfer wedge
(`chamfer_top_edge`) or soften with `soften_edges(az_max)` selecting by edge
direction; never let a failed fillet abort the whole build — try/except and
warn.

## 8. Threads
Model helical threads only behind a switch (`model_threads`); default off for
speed and validity. Plain pilot holes + a note ("tap M5") are what vendors want.

## 9. Left/right parts
Don't mirror (creates a second SKU). Design flip-symmetric about a midplane and
**rotate 180°** (`shape.rotate(Vector(0,0,0), Vector(0,0,1), 180)`); prove it
with a symmetry residual (see verification.md).

## 10. Group visibility in FreeCAD 1.x
Hiding a `DocumentObjectGroup` hides children. When isolating parts for a
render, set visibility on the leaves after the groups.

## 11. transformGeometry SHEARS booleaned shapes
`shape.transformGeometry(matrix)` on a fused/cut solid can shear it — the
tell is a bounding box √3× wider than expected. Use `Shape.translate()` /
`rotate()` instead, and bake nothing.

## 12. Feature placement after `obj.Shape = shape`
Assigning a shape whose internal Placement is set (e.g. after `translate()`)
MIRRORS that placement into `obj.Placement`. Overwriting it (`.Base = …`)
un-poses the part; composing (`pl.multiply(obj.Placement)`) doubles it.
Leave it untouched; apply layout offsets relatively: `obj.Placement.move(v)`.

## 13. Real timing-gear teeth (FCGear) you can drill
Create the feature, copy the Shape, delete the feature; all machining as Part
booleans on the copy — PartDesign pockets on gear features misbehave:
```python
from freecad.gears.commands import CreateTimingGear
gf = CreateTimingGear.create(); gf.type = "htd5"; gf.num_teeth = 44; gf.height = 16.5
doc.recompute(); gear = gf.Shape.copy(); doc.removeObject(gf.Name)
gear = gear.cut(bore).cut(holes)     # safe
```
Types: gt2 gt3 gt5 gt8 htd3 htd5 htd8.
