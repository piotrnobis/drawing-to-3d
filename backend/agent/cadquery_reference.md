# CadQuery reference — idiomatic, working examples

These are real, runnable CadQuery snippets (from the official docs). Match this
style: build features fluently off a `Workplane`, drive everything from named
dimension variables, select faces/edges with selectors, and finish with
`result = ...`.

## Workplane basics

```python
import cadquery as cq

length, height, thickness, hole_d = 80.0, 60.0, 10.0, 22.0

# box, then drill a centered hole through the top face
result = (
    cq.Workplane("XY")
    .box(length, height, thickness)
    .faces(">Z")
    .workplane()
    .hole(hole_d)
)
```

```python
# round all vertical edges
result = cq.Workplane("XY").box(3, 3, 0.5).edges("|Z").fillet(0.125)
```

## 2D profile -> extrude (lines, arcs, splines, polylines)

```python
# lines + a three-point arc, closed and extruded
result = (
    cq.Workplane("front")
    .lineTo(2.0, 0).lineTo(2.0, 1.0)
    .threePointArc((1.0, 1.5), (0.0, 1.0))
    .close()
    .extrude(0.25)
)
```

```python
# half profile via polyline, mirrored, then extruded (I-beam)
L, H, W, t = 100.0, 20.0, 20.0, 1.0
pts = [(0, H/2), (W/2, H/2), (W/2, H/2 - t), (t/2, H/2 - t),
       (t/2, t - H/2), (W/2, t - H/2), (W/2, -H/2), (0, -H/2)]
result = cq.Workplane("front").polyline(pts).mirrorY().extrude(L)
```

## Hole patterns via construction geometry

```python
# counterbored holes at the corners of a construction rectangle
result = (
    cq.Workplane("XY")
    .box(4, 2, 0.5)
    .faces(">Z").workplane()
    .rect(3.5, 1.5, forConstruction=True)   # construction rect -> its vertices
    .vertices()
    .cboreHole(0.125, 0.25, 0.125, depth=None)
)
```

## Sketch API — the CORRECT way to use hull()

`hull()` operates on the entities ALREADY ADDED to a `cq.Sketch()`. You must add
arcs / circles / segments FIRST, then call `.hull()`. Calling `.hull()` on an
empty selection (or on a `Workplane`) raises `ValueError: No entities specified`.

```python
# convex hull around two circles and a segment (a "diamond"/obround flange)
result = (
    cq.Sketch()
    .arc((0, 0), 1.0, 0.0, 360.0)      # circle as a full arc, center (0,0) r=1.0
    .arc((1, 1.5), 0.5, 0.0, 360.0)    # second circle
    .segment((0.0, 2), (-1, 3.0))
    .hull()
)
```

```python
# rectangle with filleted corners
result = cq.Sketch().rect(2, 2).vertices().fillet(0.25).reset()

# subtractive circles at the trapezoid's vertices (mode="s" = subtract)
result = cq.Sketch().trapezoid(4, 3, 90).vertices().circle(0.5, mode="s")
```

## Placing a Sketch on a face and extruding / cutting

```python
# build a sketch in place on a face, then extrude
result = (
    cq.Workplane().box(5, 5, 1)
    .faces(">Z").sketch()
    .regularPolygon(2, 3)
    .finalize()
    .extrude(0.5)
)
```

```python
# reuse a pre-built sketch via placeSketch, then cut
s = cq.Sketch().trapezoid(3, 1, 110).vertices().fillet(0.2)
result = (
    cq.Workplane().box(5, 5, 5)
    .faces(">X").workplane()
    .placeSketch(s)
    .cutThruAll()
)
```
