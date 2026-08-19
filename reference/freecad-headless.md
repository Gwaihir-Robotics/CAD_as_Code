# FreeCAD headless recipes (FreeCAD 1.x, macOS paths shown)

## Run
```sh
FC=/Applications/FreeCAD.app/Contents/Resources/bin
$FC/freecadcmd macros/MyGenerator.FCMacro           # headless, prints to stdout
$FC/freecadcmd -c "import FreeCAD; print(FreeCAD.Version()[:3])"
$FC/freecad tools/render_views.FCMacro              # GUI mode (screenshots)
```
Filter the noise: `2>&1 | grep -v "NOTICE\|%)"`.

## Skeleton
```python
import os, FreeCAD as App, Part
from FreeCAD import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
OUT_DIR = os.path.join(PROJECT_DIR, "generated"); os.makedirs(OUT_DIR, exist_ok=True)

doc = App.newDocument("MyDoc")           # or getDocument + clear objects
obj = doc.addObject("Part::Feature", "Plate"); obj.Shape = solid
doc.recompute()
for o in doc.Objects: o.purgeTouched()   # no "recompute?" prompt on open
doc.saveAs(os.path.join(OUT_DIR, "MyDoc.FCStd"))
solid.exportStep(os.path.join(OUT_DIR, "Plate.step"))
```

## Visibility of headless saves
Headless FCStd files have no `GuiDocument.xml`; the GUI then creates hidden view
providers. Append one after saving:
```python
if not App.GuiUp:
    import zipfile
    vps = "".join('<ViewProvider name="%s" expanded="0"><Properties Count="1" '
                  'TransientCount="0"><Property name="Visibility" type="App::PropertyBool">'
                  '<Bool value="true"/></Property></Properties></ViewProvider>' % o.Name
                  for o in doc.Objects)
    xml = ("<?xml version='1.0' encoding='utf-8'?>\n<Document SchemaVersion=\"1\">"
           "<ViewProviderData Count=\"%d\">%s</ViewProviderData></Document>\n" % (len(doc.Objects), vps))
    with zipfile.ZipFile(fcstd, "a") as z:
        if "GuiDocument.xml" not in z.namelist():
            z.writestr("GuiDocument.xml", xml)
```
Also set `obj.Visibility = True` at App level. Remind the user: FreeCAD keeps a
stale in-memory copy — close and reopen the FCStd after regenerating.

## STEP in / out
```python
import Part
shape = Part.Shape(); shape.read(step_path)      # or Part.read(step_path)
solids = shape.Solids                            # vendor files: many solids
Part.export([obj], out_path)                     # or shape.exportStep(path)
```
- Multi-solid vendor parts: create one `Part::Feature` per solid inside a
  `App::DocumentObjectGroup`; place with `feat.Placement = pose.multiply(feat.Placement)`.
- Round-trip check: `Part.read(out).Solids` non-empty and volume matches.

## Measuring vendor geometry
```python
bb = shape.BoundBox                              # extents in its own frame
for f in shape.Faces:                            # holes = cylindrical faces
    if f.Surface.TypeId == "Part::GeomCylinder": print(f.Surface.Center, f.Surface.Radius*2)
wires = shape.slice(Vector(0,0,1), z)            # section at height z
```

## Spreadsheet-driven params
```python
sheet = doc.addObject("Spreadsheet::Sheet", "Params")
sheet.set("A1", "name"); sheet.set("B1", "value"); sheet.set("C1", "comment")
for i, (k, v, c) in enumerate(GLOBALS, start=2):
    sheet.set("A%d" % i, k); sheet.set("B%d" % i, str(v)); sheet.set("C%d" % i, c)
    sheet.setAlias("B%d" % i, k)
doc.recompute()
val = sheet.get("riser_height")
```

## Rendering (GUI macro)
```python
import FreeCADGui as Gui
v = Gui.getDocument(doc.Name).activeView()
v.setCameraType("Orthographic")
v.setCameraOrientation(App.Rotation(matrix_from_dir(dx, dy, dz)))  # see fly/tools/render_views.FCMacro
v.fitAll(); Gui.updateGui()
v.saveImage(path, 1800, 1200, "White")
Gui.getMainWindow().close()                      # exit when done
```
Toggle `obj.ViewObject.Visibility` to isolate parts. FreeCAD's stock
"isometric" may look from the wrong side — pick the camera direction explicitly.

## Gotcha: `sys.exit()` swallows your output
`freecadcmd` exits without flushing stdout when a macro calls `sys.exit()`.
Call `sys.stdout.flush()` first (or avoid `sys.exit` and print a `RESULT` line).

## Saved camera: make the file open fit-all, oriented
A headless-saved FCStd opens with FreeCAD's default camera. Bake one into the
same `GuiDocument.xml` you write for visibility. FreeCAD only honours its own
format — the `<Camera>` element goes **after** `</ViewProviderData>` and the
settings string uses `&#10;` for newlines (a plausible-but-different layout is
silently ignored; capture a GUI-saved file's XML if in doubt):
```python
c = scene_bb_centre; d = Vector(1, -1, 1); d.normalize()      # front-right-top, Z up
up = Vector(0, 0, 1); cx = up.cross(d); cx.normalize(); cy = d.cross(cx)
rot = App.Rotation(App.Matrix(cx.x, cy.x, d.x, 0, cx.y, cy.y, d.y, 0,
                              cx.z, cy.z, d.z, 0, 0, 0, 0, 1))
height = max(extent_along(cx), extent_along(cy)) * 1.1        # ortho fit
dist = bb.DiagonalLength; pos = c + d * dist
cam = ('<Camera settings="OrthographicCamera {&#10;  viewportMapping ADJUST_CAMERA&#10;'
       '  position %.5f %.5f %.5f&#10;  orientation %.8f %.8f %.8f  %.7f&#10;'
       '  nearDistance %.5f&#10;  farDistance %.5f&#10;  aspectRatio 1&#10;'
       '  focalDistance %.5f&#10;  height %.5f&#10;&#10;}&#10;"/>'
       % (pos.x, pos.y, pos.z, rot.Axis.x, rot.Axis.y, rot.Axis.z, rot.Angle,
          dist * 0.4, dist * 1.6, dist, height))
xml = '...<ViewProviderData ...>...</ViewProviderData>%s</Document>' % cam
```
Sanity check: direction (1,−1,1) with Z up must produce orientation
`0.7429 0.3077 0.5945 @ 1.2171` — FreeCAD's own isometric.
