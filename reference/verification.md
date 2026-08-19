# Verification patterns

Print numbers. A generator that ends with `residual 0.000` is trustworthy; one
that ends with "done" is not.

## Boolean residual (did the cut actually remove the cutter?)
```python
res = tool.common(plate).Volume
print("cutter residual %.3f mm^3" % res)      # expect 0.0
```

## Interference between mating parts
```python
inter = hrp85_body.common(plate).Volume       # expect 0
seat  = arbor.common(riser).Volume            # expect == intended seat volume, e.g. pi*r^2*5
```

## Symmetry residual (one SKU ×2)
```python
flipped = side.copy(); flipped.rotate(Vector(0,0,0), Vector(0,0,1), 180)
res = side.cut(flipped).Volume + flipped.cut(side).Volume
print("symmetry residual %.3f" % res)          # expect 0.0
```

## Expected-hole audit
```python
found = {(round(f.Surface.Center.x,1), round(f.Surface.Center.y,1), round(f.Surface.Radius*2,1))
         for f in shape.Faces if f.Surface.TypeId == "Part::GeomCylinder"}
for (x, y, d) in expected:
    assert (round(x,1), round(y,1), round(d,1)) in found, "hole D%.1f at (%.1f,%.1f) missing" % (d, x, y)
```
Also report holes that pass through a bend zone or fall closer than the
vendor's minimum hole-to-bend distance.

## Keep-out / fixture clash per SKU
```python
for sku in skus:
    clash = guide.common(riser_envelope(sku)).Volume + guide.common(arbor_envelope(sku)).Volume
    if clash > 0: print("FIXTURE CLASH %s: %.1f mm^3" % (sku, clash))
```
A clash the generator reports is a design decision surfaced, not a bug hidden.

## STEP round-trip
```python
back = Part.read(step_path)
assert back.Solids and abs(back.Volume - solid.Volume) < 1e-3
```

## Mass/volume sanity
Compare `solid.Volume` to a hand estimate (plate: L×W×T minus holes). A 10%
surprise means a cutter missed or doubled.

## Section audit
`solid.slice(Vector(0,0,1), z)` at plate mid-thickness → count wires and their
lengths; e.g. two ~308 mm wires = two silhouette cutouts present.

## Where checks live
At the end of `main()` in the generator (always run) plus optional
`tools/verify_*.py` for slower checks (STEP round-trip on every part). Fail
loudly (`App.Console.PrintWarning`/`PrintError`), never silently.
