# Technical Drawing Views Reference

A comprehensive reference of every view type that can appear in a 2D technical drawing,
including how to identify each type visually and programmatically.

---

## 1. Principal Orthographic Views

The six views obtained by projecting the part onto each face of its bounding box.
In practice, drawings use 2–4 of these.

| View | Also called | Projection direction | Typical position on sheet (3rd-angle) |
|------|-------------|---------------------|---------------------------------------|
| Front | Elevation, Main view | −Y | Centre left |
| Back | Rear elevation | +Y | Far right or far left |
| Top | Plan view | −Z (looking down) | Above front view |
| Bottom | Underside | +Z (looking up) | Below front view |
| Right side | Right elevation | +X | Right of front view |
| Left side | Left elevation | −X | Left of front view |

### Identification cues
- Arranged in a regular grid on the sheet with consistent spacing.
- Labelled with a view title (`FRONT`, `TOP`, `RIGHT SIDE`, etc.) or no label if arrangement makes it obvious.
- Projection symbol in or near the title block indicates **first-angle** (ISO) or **third-angle** (ANSI/ASME).

### First-Angle vs Third-Angle layout

```
Third-Angle (ANSI — USA, Canada)       First-Angle (ISO — Europe, international)

           [Top]                                    [Bottom]
  [Left]  [Front]  [Right]              [Right]    [Front]   [Left]
           [Bottom]                                 [Top]
```

---

## 2. Auxiliary Views

Used when a feature lies on a **slanted (oblique) face** that is not parallel to any
principal plane. The projection direction is perpendicular to that face's true normal,
so the feature appears in its true shape and size.

| Type | Description |
|------|-------------|
| Primary auxiliary | Face inclined to one principal plane; parallel to the other two |
| Secondary auxiliary | Face inclined to two principal planes (doubly oblique) |

### Identification cues
- A **viewing arrow** points at the slanted face, labelled with a letter (e.g. `VIEW A`).
- The auxiliary view is placed in the direction the arrow points and labelled `A`.
- Projection lines fan out from the inclined surface to the auxiliary view.
- Often only the true-shape feature is drawn; the rest of the part is omitted.

---

## 3. Section Views

The model is cut by a **cutting plane**; the cross-sectional profile is shown with
hatching (thin 45° lines). Features behind the cut plane may still be visible.

### 3.1 Full Section

The cutting plane passes completely through the part along a single flat plane.

```
Cutting plane symbol:   ──── A ────►◄──── A ────
Resulting view label:   SECTION A-A
```

- Identified by a thick chain line (cutting plane line) with arrows showing the view direction.
- Entire interior is exposed.

---

### 3.2 Half Section

Used for **symmetric parts** only. Half is cut, half is left intact.
One view simultaneously shows the exterior profile and the interior cross-section.

```
   Exterior  │  Interior
   (uncut)   │  (hatched)
             │
           axis of symmetry
```

- Cutting plane line runs only to the axis of symmetry.
- The dividing line between the two halves is the **centre line** (thin dash-dot), not a solid line.

---

### 3.3 Offset Section

The cutting plane **steps** (offsets) to pass through multiple features that do not
lie in a single flat plane (e.g. three bolt holes at different radii).

```
    ┌────────┐
    │        │   cutting plane steps to include all three holes
    │   ┐    │
    │   └────┘
```

- Identified by a bent cutting plane line with bend points marked by dots or small squares.
- The view appears as if the part were cut by one continuous plane (bends are not shown as lines in the view).
- Label: `SECTION B-B` (or similar).

---

### 3.4 Aligned Section

Used for **parts with features arranged on a bolt circle or at an angle** (e.g. spokes,
ribs, holes on a flange). The cutting plane rotates to include the feature, then the
cut is "unfolded" to a flat plane before projecting.

- Identified by an angled cutting plane line with rotation arrow.
- The angled feature appears at its true shape, not foreshortened.
- Common in flanges, wheels, pump bodies.

---

### 3.5 Revolved Section

The cross-section profile is rotated **90° in place** and drawn directly on top of the
parent view (e.g. showing the cross-section of a spoke or handle within the front view).

```
   ┌────────── ⊂oval⊃ ──────────┐
   front view with cross-section
   shape superimposed on it
```

- No separate view box — the profile sits on the parent view.
- Thin solid lines outline the revolved section; the rest of the part is shown behind it.

---

### 3.6 Removed Section

Same as revolved but drawn **outside** the parent view, connected to it by a centre line
or reference label.

- Placed anywhere on the sheet with a label (`SECTION C-C`).
- Used when the profile is too complex to draw in-place without cluttering the parent view.

---

### 3.7 Broken-Out Section

Only a **small, irregularly bounded area** is cut away to expose a specific detail
(e.g. showing the keyway inside a shaft without cutting the whole part).

```
   ──────╮ ╭─── jagged break line
         │ │
      [internal detail shown with hatching]
         │ │
   ──────╯ ╰───
```

- Identified by a **freehand (jagged) break line** — not a straight cutting plane.
- No cutting plane symbol, no section label.
- The removed area is bounded by an irregular wavy line.

---

### 3.8 Thin Section

Very thin parts (gaskets, sheet metal, rubber seals, structural members in cross-section)
are shown **entirely filled solid black** rather than hatched, because the wall is too
thin for hatching lines.

- Identified by solid-filled cross-section profile.
- When two thin parts touch, a thin gap (white line) separates them.

---

## 4. Detail Views

An enlarged view of a small region that would be unreadable at the drawing's main scale.

```
Main view:           Detail view:
                     DETAIL A
   ○ ← circle        SCALE 4:1
   labelled A        [enlarged region]
```

### Identification cues
- A **circle** (thin solid line) drawn on the parent view encloses the region of interest.
- The circle is labelled with a letter (`A`, `B`, …).
- The detail view is labelled `DETAIL A — SCALE 4:1` (or similar scale ratio).
- The detail view has its own independent scale, always larger than the parent.

---

## 5. Pictorial Views

Non-orthographic views that give a 3D impression.

| Type | Foreshortening | Common use |
|------|---------------|------------|
| **Isometric** | Equal on all three axes (0.816 factor) | Most common in mechanical drawings |
| **Dimetric** | Two axes equal, third different | Less common |
| **Trimetric** | All three axes different | Rare |
| **Cavalier oblique** | One face true-size, depth at 45°, full scale | Furniture, woodworking |
| **Cabinet oblique** | Same but depth at half scale | Furniture |
| **One-point perspective** | One vanishing point | Architecture |
| **Two-point perspective** | Two vanishing points | Architecture, product illustration |

### Identification cues
- No cutting plane, no section arrows.
- Often placed in the upper-right corner of the sheet as an orientation reference.
- Labelled `ISOMETRIC VIEW`, `3D VIEW`, or left unlabelled.
- Dimension lines are usually absent (pictorial views are not dimensioned).

---

## 6. Broken Views

Long parts with a **uniform cross-section** (shafts, beams, rods) are shown with a
break to save sheet space. Only the ends are drawn; the middle is omitted.

```
   ├──────────╫╫──────────┤
              ↑↑
         break symbol
```

### Break symbol types by material / shape

| Symbol | Used for |
|--------|----------|
| S-curve (solid cylinder) | Solid round bar, shaft |
| Zigzag | Rectangular sections, flat bar |
| Wavy line | Wood, structural profiles |
| Figure-8 curve | Hollow tube / pipe |

### Identification cues
- Two break symbols appear at the cut points.
- An overall dimension annotation (with the true full length) bridges the break.
- The view is shorter than the actual part — always check the dimension, not the drawing length.

---

## 7. Partial Views

Only part of a **symmetric** part is drawn; the other half is implied by a symmetry axis.

```
   │         │
   │  [half  │
   │  of     │
   │  part]  │
   ├── ─ ─ ──┤  ← axis of symmetry (centre line)
```

### Identification cues
- The view terminates at a **centre line** (thin dash-dot), not at the part boundary.
- No label; the symmetry is implied.
- Sometimes a short perpendicular tick appears at each end of the centre line to emphasise it.

---

## 8. View Annotation Quick Reference

| Annotation | Meaning |
|------------|---------|
| `SECTION A-A` | Full, half, offset, or aligned section along cutting plane A-A |
| `A ──►` arrow on cutting plane | View direction for section A-A |
| `DETAIL B — SCALE 4:1` | Enlarged detail of region B |
| `VIEW C` with arrow | Auxiliary view in direction of arrow C |
| Thin 45° hatching | Cut material in a section view |
| Solid black fill | Thin section material |
| Centre line (dash-dot) | Axis of symmetry; also used as cutting plane path |
| Zigzag / S-curve line | Break in a broken view |
| Freehand wavy line | Break in a broken-out section |
| Projection symbol (cone icon) | First-angle or third-angle convention for the whole drawing |

---

## 9. Programmatic Identification in pythonOCC

| View type | Generation method |
|-----------|-----------------|
| All 6 principal views | `HLRBRep_Algo` with standard `gp_Ax2` directions — see `projection.py` |
| Arbitrary auxiliary view | Custom `gp_Ax2` normal = face's true normal |
| Full / half / offset / aligned section | `BRepAlgoAPI_Section` to get cut wires + HLR on remaining solid |
| Broken-out section | `BRepAlgoAPI_Common` with a small bounding-box cutter |
| Revolved / removed section | `BRepAlgoAPI_Section` at a plane through the feature axis |
| Detail view | Same projection, clip to a 2D bounding box region after HLR |
| Isometric / dimetric / trimetric | Diagonal `gp_Ax2` direction — isometric already in `projection.py` |
| Perspective | `HLRAlgo_Projector` perspective constructor (focal length parameter) |
| Broken view | Post-process: clip polylines at break positions, insert break symbol |
| Partial view | Post-process: clip polylines at symmetry axis |
