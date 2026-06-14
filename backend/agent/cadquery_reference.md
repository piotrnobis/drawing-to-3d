# CadQuery manual — building parametric models from engineering drawings

A condensed, high-signal guide: the mental model, a design procedure, the patterns
to use, the selectors, and the mistakes to avoid. Mirror the worked examples at the end.

## 1. Mental model
- CadQuery is a **fluent, chained** API over OpenCASCADE. Each call consumes the current
  "stack" of geometry and returns a new `Workplane`; read a chain top-to-bottom like a sentence.
- A **Workplane** is a 2D sketch plane with its own local coordinate frame. Named planes:
  `"XY"`, `"XZ"`, `"YZ"`. You draw 2D (`circle`, `rect`, `lineTo`, …) then go 3D
  (`extrude`, `revolve`, `sweep`, `loft`).
- **Local vs world coordinates:** drawing happens in the *current* workplane's local frame.
  `.workplane(offset=d)` starts a new plane parallel to the last, `d` along its normal;
  `.center(x, y)` shifts the local origin.
- **Design intent (relative positioning):** when natural, position features relative to
  geometry (`.faces(">Z").workplane().hole(d)`) so the model survives dimension changes.
  For a multi-body part, building each piece as a primitive at an **absolute** position and
  unioning is the most robust (see §2).
- **Construction geometry:** `rect(w, h, forConstruction=True).vertices()` yields points (e.g. a
  bolt pattern) without adding material.

## 2. Design procedure (drawing → solid)
1. **Datum & convention.** Z is up; the front view is the X–Z plane. Pick an origin (e.g. the
   left flange face at X=0). Define EVERY dimension as a named variable.
2. **Decompose** the part into simple pieces: slabs (`box`), discs/pipes (`cylinder`/`sweep`),
   ribs (extruded triangle), flanges (extruded profile or sketch).
3. **Build each piece as a solid** at its absolute position via `.translate((x, y, z))`, giving
   mating pieces a few-mm **overlap**.
4. **Union** all structural pieces into ONE connected solid.
5. **Cut** internal bores and bolt holes AFTER the union (so they pass through every layer).
6. **Fillet / chamfer** last: select the edges, then apply.
7. Assign the result to `result`; end with `show_object(result)`.

## 3. Build patterns
- **Primitives:** `cq.Workplane("XY").box(l, w, h)`, `.cylinder(h, r)`, `.sphere(r)`.
- **2D → 3D:** sketch then `.extrude(d)`, `.revolve(angle)`, `.sweep(path)`, `.loft()`.
- **Booleans:** `.union(other)`, `.cut(other)`, `.intersect(other)`.
- **Holes:** on a face workplane, `.hole(d)` / `.cboreHole(...)`; for patterns use a
  construction rect/circle + `.vertices()` (or `.pushPoints([...])`) then `.hole(d)`.
- **Pipes / elbows:** build the centerline with `.lineTo(...)` then `.tangentArcPoint((x, y),
  relative=False)` (or `.radiusArc((x, y), R)`) for each bend, then `.sweep` a circle along it.
  Hollow pipe = sweep OD, then cut a swept ID whose path is extended a few mm BEYOND each open
  end so the ends are truly open (annular), not capped.
- **Notch / pocket / step / slot that opens on a SPECIFIC face:** do NOT cut a free-floating box
  positioned by absolute coordinates — that repeatedly lands the opening on the WRONG side. Anchor
  the cut to the face it opens on: select that face, `.workplane()` on it, draw the profile, and
  `.cutBlind(-depth)` inward. The opening is then guaranteed on the chosen face. To leave a wall of
  thickness `t` behind the feature, make the cut depth = (face-to-far-side distance − t). Example —
  a notch opening on the BACK (`+Y`) face, leaving a `t` wall at the front:
  `part.faces(">Y").workplane().center(cx, cz).rect(w, h).cutBlind(-(depth))`. Decide the side
  deliberately: which face does the drawing show the recess/lip on? The thin remaining wall is on
  the face that stays solid; the opening is on the opposite face.
- **Uniform-wall pockets / shelling a profile:** to hollow a profile leaving an even wall `t`,
  draw the OUTER profile on a workplane, `.offset2D(-t)` to get the inner wire, extrude that as a
  separate solid and `.cut()` it (depth = pocket depth). `offset2D` lives on **Workplane**, acts on
  the pending wire, and a NEGATIVE value goes inward: `inner = outer.offset2D(-4.0)`. Prefer this
  over the Sketch class for walls — it is simpler and less error-prone. (See §6.)
- **Sketch API (a DIFFERENT API from Workplane — do not mix them):**
  - Construct `cq.Sketch()`, add faces (`.rect(w, h)`, `.circle(r)`, `.polygon(pts)`,
    `.trapezoid(...)`), place with `.placeSketch(sk)` then `.extrude(d)`.
  - **`Sketch.circle(r, mode='a')` takes a RADIUS ONLY — no center.** Position it with
    `.push([(x, y), ...])` BEFORE the `.circle`/`.rect` (default is the origin). `mode='s'`
    subtracts, `'a'` (default) adds. So a centered hole is `.push([(x, y)]).circle(r, mode='s')`,
    NOT `.circle((x, y), r)`.
  - **`Sketch.offset(d, mode='s')` needs a face/wire SELECTION first** (`ValueError: Selection is
    needed to offset` otherwise): `cq.Sketch().rect(20, 20).reset().faces().offset(-4, mode='s')`
    leaves a 4 mm ring. There is **no `Sketch.offset2D`** (that is a Workplane method).
  - `.hull()` needs entities added first (see pitfall below). `.reset()` clears the current
    selection; `.vertices()`/`.faces()` select before `.fillet`/`.offset`.

## 4. Selectors (cheat sheet)
- `">Z"` / `"<Z"` — farthest face/edge in +Z / −Z. `"|Z"` parallel to Z; `"#Z"` perpendicular
  to Z; `"+Z"` normal points +Z. `"%CIRCLE"` filters by type.
- Common: `.faces(">Z").workplane()` (top face), `.edges("|Z")` (vertical edges).
- Directional string selectors do NOT match curved edges — use `"%CIRCLE"` or `.filter(...)`.
- Multiple matches: index like `">Z[1]"`, combine with `and`/`or`/`not`/`exc`, or
  `.faces(sel).filter(lambda f: f.Center().z > 45)` for precise picks.

## 5. Pitfalls (these are the actual failures we hit — avoid them)
- **Z is up.** Named-plane normals: `"XY"`→+Z, `"XZ"`→−Y, `"YZ"`→+X. `extrude(d)` / positive
  offsets go ALONG the normal (so `"XZ"` extrudes toward −Y) — extrude negative or `.translate`
  to land on the +Y side, and keep mating parts overlapping so the union stays connected.
- **`.workplane()` takes an OFFSET float, not a plane name.** `obj.workplane(offset=10)` ✔;
  `obj.workplane("XY")` ✗ (TypeError). Start a named plane with `cq.Workplane("XY"/"XZ"/"YZ")`.
- **Elbows: never `threePointArc(mid, end)` with a hand-computed midpoint** — if `mid` is not
  exactly on the arc, OCC fails (`GC_MakeArcOfCircle … no result`) or the bend misaligns and the
  pipe disconnects. Use `tangentArcPoint`/`radiusArc` (end point only, stays tangent).
- **No `.cutDepth()`** (it doesn't exist) — use `.cut()`, `.cutBlind(-d)`, `.cutThruAll()`.
- **`.fillet(r)` / `.chamfer(c)` operate on already-SELECTED edges:** `part.edges("|Z").fillet(3)`.
  Never pass an edge list as an argument.
- **`Sketch` and `Workplane` are DIFFERENT APIs — methods do not carry over.** `.offset2D` is
  Workplane-only (`AttributeError` on a Sketch); `Sketch.circle`/`.rect` take NO center (use
  `.push([(x, y)])`), whereas `Workplane.circle(r)` draws at the current point. Calling
  `Sketch.circle((x, y), r, mode=...)` raises `got multiple values for argument 'mode'` because the
  center tuple is read as the radius and `r` as the mode. `Sketch.offset(d)` needs a `.faces()`
  selection first. When in doubt for a hollow pocket, use the Workplane `.offset2D(-t)` pattern (§6).
- **`hull()` is Sketch-only AND only hulls entities added as `.arc(...)` / `.segment(...)`.**
  `.circle()` / `.push().circle()` do NOT feed the hull (→ `ValueError: No entities specified`);
  add each circle as a full arc: `.arc(center, r, 0.0, 360.0)`, THEN `.hull()`.
- **A cut opens on the face you cut FROM — pick that face deliberately.** Cutting a free-floating
  box by absolute coordinates frequently puts the opening on the wrong side (a recurring failure:
  the notch/pocket ends up mirrored, with the thin wall on the wrong face). Anchor pockets/notches
  to a selected face + `.cutBlind(-depth)` (see §3). Before cutting, state which face the recess is
  on and which face keeps the thin wall — the drawing shows the lip/wall on the solid side.
- **Bores must OPEN where the drawing shows a hole.** A through-bore must pass entirely through
  every flange/wall it ends at, cut a few mm PAST that face — otherwise the face stays solid (a
  "blind" bore). The main bore must open at BOTH the circular flange face and the square flange
  top; a pipe end must be a hollow ring, not a solid disc.
- **Drill holes AFTER unioning** all solids; **make mating parts overlap** before union; the final
  `result` must be ONE connected solid.
- **Workplane on a face:** select a SINGLE planar face (precise selector or `.filter`) or you get
  `Selected faces must be co-planar`.
- **Don't invent methods** — stick to the documented API above.

## 6. Worked examples

```python
import cadquery as cq

# box + centered hole through the top face
result = cq.Workplane("XY").box(80, 60, 10).faces(">Z").workplane().hole(22)
```

```python
# fillet all vertical edges
result = cq.Workplane("XY").box(40, 30, 10).edges("|Z").fillet(3)
```

```python
# bolt pattern via a construction rectangle's corners
result = (
    cq.Workplane("XY").box(40, 20, 5)
    .faces(">Z").workplane()
    .rect(30, 12, forConstruction=True).vertices()
    .hole(5)
)
```

```python
# convex-hull (obround) flange: hull a Sketch, place it, extrude to a solid
sk = cq.Sketch().arc((0, 0), 12.5, 0.0, 360.0).arc((0, 17.5), 5.0, 0.0, 360.0).hull()
result = cq.Workplane("XY").placeSketch(sk).extrude(3.75)
```

```python
# notch on a CHOSEN face, leaving a thin wall on the opposite face (face-anchored, not absolute)
# flange is 25 thick in Y; we want the recess open on the BACK (+Y) face, a 10 mm wall left at front
flange = cq.Workplane("XY").box(120, 25, 80)
result = (
    flange.faces(">Y").workplane()      # work ON the back face; +depth goes INTO the part (−Y)
    .center(0, 25)                      # locate the notch on that face (local x, y = world x, z)
    .rect(70, 30)
    .cutBlind(-(25 - 10))              # cut 15 mm deep → leaves a 10 mm wall at the front face
)
```

```python
# uniform-wall pocket: hollow an arm leaving an even 4 mm wall (use Workplane offset2D)
WALL, DEPTH = 4.0, 8.5
arm = cq.Workplane("XY").polygon(8, 60).extrude(12.5)  # or any closed outer profile
inner = (
    cq.Workplane("XY").polygon(8, 60)  # SAME outer profile, redrawn
    .offset2D(-WALL)                    # negative = inward; pending wire shrinks 4 mm
    .extrude(-DEPTH, combine=False)     # standalone pocket solid, cut downward
)
result = arm.cut(inner.translate((0, 0, 12.5)))  # cut into the top face
```

```python
# Sketch the RIGHT way: profile with two subtracted holes (radius only; position via push)
sk = (
    cq.Sketch()
    .rect(40, 20)                      # outer face, centered at origin
    .push([(-12, 0), (12, 0)])         # set hole centers FIRST
    .circle(4.5, mode="s")             # radius only; mode="s" subtracts at each pushed point
    .reset()
)
result = cq.Workplane("XY").placeSketch(sk).extrude(5)
```

```python
# swept hollow pipe with a robust 90° elbow (no hand-computed arc midpoints)
import cadquery as cq

R = 18.75
Xv = 56.25 + R                          # vertical run centerline; start + R => clean quarter turn
OD, ID = 25.0, 20.0
path = (
    cq.Workplane("XZ").moveTo(0, 0)
    .lineTo(Xv - R, 0)                  # horizontal run along Z=0
    .tangentArcPoint((Xv, R), relative=False)  # tangent quarter turn up
    .lineTo(Xv, 50.0)                   # vertical run
)
outer = cq.Workplane("YZ").circle(OD / 2).sweep(path)
bore = cq.Workplane("YZ").circle(ID / 2).sweep(path)
result = outer.cut(bore)
```
