"""
zhang.py — 3D wireframe reconstruction from 2D orthographic views.

Implements Algorithm 1 of:
  Zhang et al., "Automatic 3D CAD models reconstruction from 2D orthographic
  drawings", Computers & Graphics, 2023. doi:10.1016/j.cag.2023.05.017

The algorithm pattern-matches edges across three orthographic views to recover
exact 3D wireframe geometry without any machine-learning component.  The output
wireframe.json can be injected into the CadQuery agent (--wireframe flag) to
give the model precise dimension data instead of reading from pixels.

Coordinate convention (matches projection.py)
----------------------------------------------
  front view : u = x,  v = z   (looking along −Y)
  top   view : u = x,  v = y   (looking along +Z)
  right view : u = y,  v = z   (looking along +X)

Input
-----
Three _edges.json files written by  projection.py --save-json --views front,top,right:

  python projection.py part.stp --views front,top,right --save-json --out /tmp/views/
  python zhang.py /tmp/views/part_front_edges.json \\
                  /tmp/views/part_top_edges.json   \\
                  /tmp/views/part_right_edges.json \\
                  [--out wireframe.json] [--eps 0.01] [--viz]

Output: wireframe.json  (list of 3D edges)
        wireframe.png   (3D preview, only with --viz)
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default matching tolerance as a fraction of the model's overall bounding box.
# Paper uses 0.005; 0.01 is more robust for projection.py's discretised curves.
DEFAULT_EPS_T: float = 0.01

# Axis-angle threshold (degrees): edge classified as Px/Py/Pz if its angle
# from the axis is ≤ this value.
AXIS_ANGLE_TOL: float = 5.0

# An edge whose bounding box in both axes is < VERTEX_FRAC * ε is treated as
# a projected vertex (Pt) for L1/L2/L3 patterns.
VERTEX_FRAC: float = 2.0

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

FFlag = Literal["Px", "Py", "Pz", "I", "A", "Pt"]


@dataclass
class Edge2D:
    """One 2D edge primitive from an orthographic view JSON."""
    view: str            # "front" | "top" | "right"
    u_axis: str          # 3D axis name for u-coordinate: "x" | "y" | "z"
    v_axis: str          # 3D axis name for v-coordinate: "x" | "y" | "z"
    pts: list[tuple[float, float]]   # sampled (u, v) pairs
    visible: bool = True

    # Derived — filled by _annotate()
    flag: FFlag = field(default="I")
    # Bounding box in 3D-axis names → (min, max)
    bbox: dict[str, tuple[float, float]] = field(default_factory=dict)
    # Circle fit (for A-flagged edges)
    circle: dict | None = field(default=None)  # {"cx","cy","r","a0","a1"}

    # Endpoints (first and last point in the polyline)
    @property
    def p0(self) -> tuple[float, float]:
        return self.pts[0]

    @property
    def p1(self) -> tuple[float, float]:
        return self.pts[-1]

    def _to_3d_coords(self) -> tuple[np.ndarray, np.ndarray]:
        """Return all points as 3D numpy arrays (unknown axis set to 0)."""
        u_vals = np.array([p[0] for p in self.pts])
        v_vals = np.array([p[1] for p in self.pts])
        coords = np.zeros((len(self.pts), 3))
        axis_idx = {"x": 0, "y": 1, "z": 2}
        coords[:, axis_idx[self.u_axis]] = u_vals
        coords[:, axis_idx[self.v_axis]] = v_vals
        return coords, axis_idx

    def compute_bbox(self) -> None:
        """Bounding box in 3D-axis frame (e.g. {"x": (x0,x1), "z": (z0,z1)})."""
        us = [p[0] for p in self.pts]
        vs = [p[1] for p in self.pts]
        self.bbox = {
            self.u_axis: (min(us), max(us)),
            self.v_axis: (min(vs), max(vs)),
        }


@dataclass
class Edge3D:
    """A reconstructed 3D edge."""
    pattern: str                      # e.g. "L1", "C1"
    kind: Literal["line", "arc"]
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    # For arcs: center and radius in the plane
    arc_center: tuple[float, float, float] | None = None
    arc_radius: float = 0.0
    arc_normal: tuple[float, float, float] | None = None  # plane normal


# ---------------------------------------------------------------------------
# SVG / JSON loading
# ---------------------------------------------------------------------------

def load_view(path: str | Path) -> list[Edge2D]:
    """Load an _edges.json file written by projection.py --save-json."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    view   = data["view"]
    u_axis = data["u_axis"]
    v_axis = data["v_axis"]
    edges: list[Edge2D] = []
    for vis, polylines in [(True, data["visible"]), (False, data["hidden"])]:
        for poly in polylines:
            pts = [(float(p[0]), float(p[1])) for p in poly]
            if len(pts) < 2:
                continue
            e = Edge2D(view=view, u_axis=u_axis, v_axis=v_axis,
                       pts=pts, visible=vis)
            e.compute_bbox()
            edges.append(e)
    return edges


# ---------------------------------------------------------------------------
# Feature flag assignment
# ---------------------------------------------------------------------------

def _fit_circle(pts: list[tuple[float, float]]) -> dict | None:
    """Least-squares circle fit using algebraic method (Kåsa 1976).
    Returns {"cx", "cy", "r", "a0", "a1"} or None if the fit is poor."""
    if len(pts) < 4:
        return None
    arr = np.array(pts, dtype=float)
    x, y = arr[:, 0], arr[:, 1]
    # Kåsa: minimise (xi-cx)²+(yi-cy)²-r²  → linear system
    A = np.column_stack([x, y, np.ones(len(x))])
    b = x**2 + y**2
    try:
        result, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    cx, cy = result[0] / 2, result[1] / 2
    r = math.sqrt(result[2] + cx**2 + cy**2)
    if r < 1e-9:
        return None
    # Residuals
    res = np.sqrt((x - cx)**2 + (y - cy)**2) - r
    if np.std(res) > 0.05 * r:   # more than 5 % of radius → bad fit
        return None
    # Sagitta check: reject nearly-flat arcs (projections of circles seen edge-on).
    # If the arc's height (sagitta) is < 2 % of the chord, it's effectively a line.
    chord = math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
    if chord > 1e-9:
        sagitta = r - math.sqrt(max(0.0, r**2 - (chord / 2)**2))
        if sagitta / chord < 0.02:
            return None
    a0 = math.degrees(math.atan2(pts[0][1]  - cy, pts[0][0]  - cx)) % 360
    a1 = math.degrees(math.atan2(pts[-1][1] - cy, pts[-1][0] - cx)) % 360
    return {"cx": cx, "cy": cy, "r": r, "a0": a0, "a1": a1}


def annotate(edges: list[Edge2D]) -> None:
    """Assign feature flags and circle fits to every edge in-place."""
    for e in edges:
        if len(e.pts) > 3:
            circ = _fit_circle(e.pts)
            if circ is not None:
                # Guard against classifying a nearly-flat arc as a circle.
                # A circle projected edge-on (e.g. rim circle seen from front)
                # has near-zero extent in one axis → treat it as a line instead.
                u_ext = e.bbox[e.u_axis][1] - e.bbox[e.u_axis][0]
                v_ext = e.bbox[e.v_axis][1] - e.bbox[e.v_axis][0]
                max_ext = max(u_ext, v_ext, 1e-9)
                min_ext = min(u_ext, v_ext)
                if min_ext / max_ext >= 0.05:
                    e.flag   = "A"
                    e.circle = circ
                    continue
                # fall through to linear classification below

        # Linear edge — classify by orientation
        du = e.p1[0] - e.p0[0]
        dv = e.p1[1] - e.p0[1]
        length = math.hypot(du, dv)
        if length < 1e-9:
            e.flag = "Pt"
            continue

        angle_from_u = abs(math.degrees(math.atan2(abs(dv), abs(du))))
        # angle_from_u ∈ [0, 90]  (0 = horizontal = along u_axis)
        if angle_from_u <= AXIS_ANGLE_TOL:            # ~horizontal → u_axis
            e.flag = {"x": "Px", "y": "Py", "z": "Pz"}[e.u_axis]
        elif angle_from_u >= 90.0 - AXIS_ANGLE_TOL:  # ~vertical  → v_axis
            e.flag = {"x": "Px", "y": "Py", "z": "Pz"}[e.v_axis]
        else:
            e.flag = "I"


# ---------------------------------------------------------------------------
# Normalisation & tolerance
# ---------------------------------------------------------------------------

def compute_epsilon(all_edges: list[list[Edge2D]], eps_t: float) -> float:
    """Global ε = eps_t × max side of 3D bounding box."""
    mins = {"x": float("inf"),  "y": float("inf"),  "z": float("inf")}
    maxs = {"x": float("-inf"), "y": float("-inf"), "z": float("-inf")}
    for view_edges in all_edges:
        for e in view_edges:
            for ax, (lo, hi) in e.bbox.items():
                mins[ax] = min(mins[ax], lo)
                maxs[ax] = max(maxs[ax], hi)
    extents = [maxs[ax] - mins[ax] for ax in ("x", "y", "z")
               if mins[ax] < float("inf")]
    max_ext = max(extents) if extents else 1.0
    return eps_t * max_ext


# ---------------------------------------------------------------------------
# 1D interval matching helpers
# ---------------------------------------------------------------------------

def _interval_match(a: tuple[float, float], b: tuple[float, float],
                    eps: float) -> bool:
    """True if two 1D intervals [a0,a1] and [b0,b1] match within ε."""
    return abs(a[0] - b[0]) <= eps and abs(a[1] - b[1]) <= eps


def _value_match(a: tuple[float, float], b: tuple[float, float],
                 eps: float) -> bool:
    """True if two (near-zero-width) intervals represent the same value."""
    return abs((a[0] + a[1]) / 2 - (b[0] + b[1]) / 2) <= eps


# ---------------------------------------------------------------------------
# 3D coordinate reconstruction per pattern
# ---------------------------------------------------------------------------

def _mid(bbox: dict, axis: str) -> float:
    lo, hi = bbox[axis]
    return (lo + hi) / 2.0


def _reconstruct_line(pattern: str,
                      ef: Edge2D, et: Edge2D, er: Edge2D | None,
                      ) -> Edge3D | None:
    """Reconstruct a 3D line from (front, top, right) triplet.
    er may be None for patterns where the right view contributes a vertex.
    """
    # We know:
    #   front : u=x, v=z
    #   top   : u=x, v=y
    #   right : u=y, v=z

    if pattern == "L1":
        # Both horizontal: edge parallel to X axis.  y from top, z from front.
        x0, x1 = ef.bbox["x"]
        y = _mid(et.bbox, "y")
        z = _mid(ef.bbox, "z")
        return Edge3D("L1", "line", (x0, y, z), (x1, y, z))

    if pattern == "L2":
        # Both vertical: edge parallel to Y axis.  x from front/top, z from right.
        y0, y1 = et.bbox["y"]
        x = _mid(ef.bbox, "x")
        z = _mid(er.bbox, "z") if er else _mid(ef.bbox, "z")
        return Edge3D("L2", "line", (x, y0, z), (x, y1, z))

    if pattern == "L3":
        # Both vertical (z axis): edge parallel to Z axis.  x from front, y from top.
        z0, z1 = ef.bbox["z"]
        x = _mid(ef.bbox, "x")
        y = _mid(et.bbox, "y")
        return Edge3D("L3", "line", (x, y, z0), (x, y, z1))

    if pattern == "L4":
        # front=Pz, top=Py → constant x; y from top v-range, z from front v-range.
        x = _mid(ef.bbox, "x")   # front and top share x
        y0, y1 = et.bbox["y"]
        z0, z1 = ef.bbox["z"]
        return Edge3D("L4", "line", (x, y0, z0), (x, y1, z1))

    if pattern == "L5":
        # top=Px, right=Pz → constant y; x from top u-range, z from right v-range.
        y = _mid(et.bbox, "y")
        x0, x1 = et.bbox["x"]
        z0, z1 = er.bbox["z"]
        return Edge3D("L5", "line", (x0, y, z0), (x1, y, z1))

    if pattern == "L6":
        # front=Px, right=Py → constant z; x from front u-range, y from right u-range.
        z = _mid(ef.bbox, "z")
        x0, x1 = ef.bbox["x"]
        y0, y1 = er.bbox["y"]
        return Edge3D("L6", "line", (x0, y0, z), (x1, y1, z))

    if pattern == "L7":
        # All inclined: general space diagonal.
        # x from front/top (shared), y from top/right (shared), z from front/right.
        x0, x1 = ef.bbox["x"]
        y0, y1 = et.bbox["y"]
        z0, z1 = ef.bbox["z"]
        return Edge3D("L7", "line", (x0, y0, z0), (x1, y1, z1))

    return None


def _reconstruct_arc(pattern: str,
                     ef: Edge2D, et: Edge2D, er: Edge2D) -> Edge3D | None:
    """Reconstruct a 3D arc/circle from a matched triplet."""
    if pattern == "C1":
        # Arc in XY plane (z = const). front=Px→z const, top=A→circle in xy.
        c = et.circle
        if c is None:
            return None
        z = _mid(ef.bbox, "z")
        return Edge3D("C1", "arc",
                      start=_circle_pt(c["cx"], c["cy"], c["r"], z, c["a0"], "xy"),
                      end  =_circle_pt(c["cx"], c["cy"], c["r"], z, c["a1"], "xy"),
                      arc_center=(c["cx"], c["cy"], z),
                      arc_radius=c["r"],
                      arc_normal=(0.0, 0.0, 1.0))

    if pattern == "C2":
        # Arc in XZ plane (y = const). top=Px→y const, front=A→circle in xz.
        c = ef.circle
        if c is None:
            return None
        y = _mid(et.bbox, "y")
        return Edge3D("C2", "arc",
                      start=_circle_pt(c["cx"], c["cy"], c["r"], y, c["a0"], "xz"),
                      end  =_circle_pt(c["cx"], c["cy"], c["r"], y, c["a1"], "xz"),
                      arc_center=(c["cx"], y, c["cy"]),
                      arc_radius=c["r"],
                      arc_normal=(0.0, 1.0, 0.0))

    if pattern == "C3":
        # Arc in YZ plane (x = const). front=Pz→x const, top=Py→x const, right=A.
        c = er.circle
        if c is None:
            return None
        x = _mid(ef.bbox, "x")
        return Edge3D("C3", "arc",
                      start=_circle_pt(c["cx"], c["cy"], c["r"], x, c["a0"], "yz"),
                      end  =_circle_pt(c["cx"], c["cy"], c["r"], x, c["a1"], "yz"),
                      arc_center=(x, c["cx"], c["cy"]),
                      arc_radius=c["r"],
                      arc_normal=(1.0, 0.0, 0.0))

    return None


def _circle_pt(cu: float, cv: float, r: float, const: float,
               angle_deg: float, plane: str) -> tuple[float, float, float]:
    """Point on a circle (center cu,cv, radius r) in the given plane at angle_deg."""
    ru = r * math.cos(math.radians(angle_deg))
    rv = r * math.sin(math.radians(angle_deg))
    if plane == "xy":
        return (cu + ru, cv + rv, const)
    if plane == "xz":
        return (cu + ru, const, cv + rv)
    # "yz"
    return (const, cu + ru, cv + rv)


# ---------------------------------------------------------------------------
# Algorithm 1 — Pattern matching
# ---------------------------------------------------------------------------

def match_patterns(front_edges: list[Edge2D],
                   top_edges:   list[Edge2D],
                   right_edges: list[Edge2D],
                   eps: float) -> list[Edge3D]:
    """
    Match triplets of 2D edges across three views using Table 1 patterns.

    Matching rules (shared 3D axes between view pairs):
      front ↔ top   : compare x-ranges  (both have u=x)
      front ↔ right : compare z-ranges  (both have v=z)
      top   ↔ right : compare y-ranges  (top v=y, right u=y)
    """
    edges_3d: list[Edge3D] = []

    # Pre-group by flag for faster lookup
    def by_flag(edges: list[Edge2D]) -> dict[str, list[Edge2D]]:
        out: dict[str, list[Edge2D]] = {}
        for e in edges:
            out.setdefault(e.flag, []).append(e)
        return out

    ff = by_flag(front_edges)
    tf = by_flag(top_edges)
    rf = by_flag(right_edges)

    def _get(d: dict, *keys: str) -> list[Edge2D]:
        out: list[Edge2D] = []
        for k in keys:
            out.extend(d.get(k, []))
        return out

    def front_top_x_match(ef: Edge2D, et: Edge2D) -> bool:
        return _interval_match(ef.bbox["x"], et.bbox["x"], eps)

    def front_right_z_match(ef: Edge2D, er: Edge2D) -> bool:
        return _interval_match(ef.bbox["z"], er.bbox["z"], eps)

    def top_right_y_match(et: Edge2D, er: Edge2D) -> bool:
        return _interval_match(et.bbox["y"], er.bbox["y"], eps)

    # ── L1: front=Px, top=Px, right=Pt  (edge ‖ X axis) ───────────────────
    for ef in _get(ff, "Px"):
        for et in _get(tf, "Px"):
            if not front_top_x_match(ef, et):
                continue
            # right-view vertex is optional — y from top, z from front
            edge = _reconstruct_line("L1", ef, et, None)
            if edge:
                edges_3d.append(edge)

    # ── L2: front=Pt, top=Py, right=Py  (edge ‖ Y axis) ───────────────────
    for et in _get(tf, "Py"):
        for er in _get(rf, "Py"):
            if not top_right_y_match(et, er):
                continue
            # front contributes a vertex: x from top, z from right
            # Find any front vertex (Pt or near-pt) at (x_mid, z_mid)
            x_check = (et.bbox["x"][0] + et.bbox["x"][1]) / 2
            z_check = (er.bbox["z"][0] + er.bbox["z"][1]) / 2
            # Use the approximate x/z to reconstruct (no front-vertex search)
            edge = _reconstruct_line("L2", _fake_front(x_check, z_check), et, er)
            if edge:
                edges_3d.append(edge)

    # ── L3: front=Pz, top=Pt, right=Pz  (edge ‖ Z axis) ───────────────────
    for ef in _get(ff, "Pz"):
        for er in _get(rf, "Pz"):
            if not front_right_z_match(ef, er):
                continue
            # top contributes a vertex: x from front, y from right
            x_check = (ef.bbox["x"][0] + ef.bbox["x"][1]) / 2
            y_check = (er.bbox["y"][0] + er.bbox["y"][1]) / 2
            edge = _reconstruct_line("L3", ef, _fake_top(x_check, y_check), er)
            if edge:
                edges_3d.append(edge)

    # ── L4: front=Pz, top=Py, right=I  (edge in YZ plane, constant x) ─────
    for ef in _get(ff, "Pz"):
        for et in _get(tf, "Py"):
            if not front_top_x_match(ef, et):
                continue
            for er in _get(rf, "I"):
                if not front_right_z_match(ef, er):
                    continue
                if not top_right_y_match(et, er):
                    continue
                edge = _reconstruct_line("L4", ef, et, er)
                if edge:
                    edges_3d.append(edge)

    # ── L5: front=I, top=Px, right=Pz  (edge in XZ plane, constant y) ─────
    for et in _get(tf, "Px"):
        for er in _get(rf, "Pz"):
            if not top_right_y_match(et, er):
                continue
            for ef in _get(ff, "I"):
                if not front_top_x_match(ef, et):
                    continue
                if not front_right_z_match(ef, er):
                    continue
                edge = _reconstruct_line("L5", ef, et, er)
                if edge:
                    edges_3d.append(edge)

    # ── L6: front=Px, top=I, right=Py  (edge in XY plane, constant z) ─────
    for ef in _get(ff, "Px"):
        for er in _get(rf, "Py"):
            if not front_right_z_match(ef, er):
                continue
            for et in _get(tf, "I"):
                if not front_top_x_match(ef, et):
                    continue
                if not top_right_y_match(et, er):
                    continue
                edge = _reconstruct_line("L6", ef, et, er)
                if edge:
                    edges_3d.append(edge)

    # ── L7: front=I, top=I, right=I  (general space diagonal) ─────────────
    for ef in _get(ff, "I"):
        for et in _get(tf, "I"):
            if not front_top_x_match(ef, et):
                continue
            for er in _get(rf, "I"):
                if not front_right_z_match(ef, er):
                    continue
                if not top_right_y_match(et, er):
                    continue
                edge = _reconstruct_line("L7", ef, et, er)
                if edge:
                    edges_3d.append(edge)

    # ── C1: top=A, front=Px, right=Py  (arc in XY plane, constant z) ──────
    for et in _get(tf, "A"):
        for ef in _get(ff, "Px"):
            if not front_top_x_match(ef, et):
                continue
            for er in _get(rf, "Py"):
                if not top_right_y_match(et, er):
                    continue
                if not front_right_z_match(ef, er):
                    continue
                edge = _reconstruct_arc("C1", ef, et, er)
                if edge:
                    edges_3d.append(edge)

    # ── C2: front=A, top=Px, right=Pz  (arc in XZ plane, constant y) ──────
    for ef in _get(ff, "A"):
        for et in _get(tf, "Px"):
            if not front_top_x_match(ef, et):
                continue
            for er in _get(rf, "Pz"):
                if not front_right_z_match(ef, er):
                    continue
                if not top_right_y_match(et, er):
                    continue
                edge = _reconstruct_arc("C2", ef, et, er)
                if edge:
                    edges_3d.append(edge)

    # ── C3: front=Pz, top=Py, right=A  (arc in YZ plane, constant x) ──────
    for ef in _get(ff, "Pz"):
        for et in _get(tf, "Py"):
            if not front_top_x_match(ef, et):
                continue
            for er in _get(rf, "A"):
                if not front_right_z_match(ef, er):
                    continue
                if not top_right_y_match(et, er):
                    continue
                edge = _reconstruct_arc("C3", ef, et, er)
                if edge:
                    edges_3d.append(edge)

    return edges_3d


def _fake_front(x: float, z: float) -> Edge2D:
    """Synthetic front-view Edge2D at a single point (for L2/L3 vertex proxy)."""
    e = Edge2D("front", "x", "z", [(x, z), (x, z)])
    e.bbox = {"x": (x, x), "z": (z, z)}
    e.flag = "Pt"
    return e


def _fake_top(x: float, y: float) -> Edge2D:
    """Synthetic top-view Edge2D at a single point (for L3 vertex proxy)."""
    e = Edge2D("top", "x", "y", [(x, y), (x, y)])
    e.bbox = {"x": (x, x), "y": (y, y)}
    e.flag = "Pt"
    return e


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _edge_key(e: Edge3D, eps: float) -> tuple:
    """Round coordinates to ε grid for hashing."""
    def rnd(v: float) -> int:
        return round(v / eps) if eps > 0 else round(v, 6)
    pts = sorted([e.start, e.end])
    return (e.pattern[0], tuple(rnd(c) for c in pts[0]),
                           tuple(rnd(c) for c in pts[1]))


def deduplicate(edges: list[Edge3D], eps: float) -> list[Edge3D]:
    seen: set = set()
    out: list[Edge3D] = []
    for e in edges:
        k = _edge_key(e, eps)
        if k not in seen:
            seen.add(k)
            out.append(e)
    return out


# ---------------------------------------------------------------------------
# Optional 3D visualisation
# ---------------------------------------------------------------------------

def visualise(edges: list[Edge3D], out_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    for e in edges:
        if e.kind == "line":
            xs = [e.start[0], e.end[0]]
            ys = [e.start[1], e.end[1]]
            zs = [e.start[2], e.end[2]]
            ax.plot(xs, ys, zs, color="steelblue", linewidth=1.0)
        elif e.kind == "arc" and e.arc_center:
            cx, cy, cz = e.arc_center
            r = e.arc_radius
            n = e.arc_normal or (0, 0, 1)
            # Sample the arc
            a0_deg = math.degrees(math.atan2(
                e.start[2 if n == (0,0,1) else 1] - (cz if n == (0,0,1) else cy),
                e.start[0] - cx))
            a1_deg = math.degrees(math.atan2(
                e.end[2 if n == (0,0,1) else 1] - (cz if n == (0,0,1) else cy),
                e.end[0] - cx))
            angles = np.linspace(math.radians(a0_deg), math.radians(a1_deg), 40)
            if tuple(n) == (0, 0, 1):
                xs = cx + r * np.cos(angles)
                ys = cy + r * np.sin(angles)
                zs = np.full_like(angles, cz)
            elif tuple(n) == (0, 1, 0):
                xs = cx + r * np.cos(angles)
                ys = np.full_like(angles, cy)
                zs = cz + r * np.sin(angles)
            else:
                xs = np.full_like(angles, cx)
                ys = cy + r * np.cos(angles)
                zs = cz + r * np.sin(angles)
            ax.plot(xs, ys, zs, color="darkorange", linewidth=1.0)

    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    ax.set_title(f"3D Wireframe  ({len(edges)} edges)")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def to_dict(edges: list[Edge3D]) -> list[dict]:
    out = []
    for i, e in enumerate(edges):
        d: dict = {
            "id": i,
            "pattern": e.pattern,
            "kind": e.kind,
            "start": [round(c, 4) for c in e.start],
            "end":   [round(c, 4) for c in e.end],
        }
        if e.arc_center:
            d["arc_center"] = [round(c, 4) for c in e.arc_center]
            d["arc_radius"] = round(e.arc_radius, 4)
            d["arc_normal"] = list(e.arc_normal) if e.arc_normal else None
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Reconstruct 3D wireframe from three orthographic view JSONs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("front", help="front_edges.json  (u=x, v=z)")
    p.add_argument("top",   help="top_edges.json    (u=x, v=y)")
    p.add_argument("right", help="right_edges.json  (u=y, v=z)")
    p.add_argument("--out",   default="wireframe.json",
                   help="Output JSON path (default: wireframe.json)")
    p.add_argument("--eps",   type=float, default=DEFAULT_EPS_T,
                   help=f"Matching tolerance fraction (default: {DEFAULT_EPS_T})")
    p.add_argument("--viz",   action="store_true",
                   help="Also save a wireframe.png 3D preview")
    p.add_argument("--all-edges", action="store_true",
                   help="Include hidden edges in matching (default: visible only)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print("Loading views...")
    front_all = load_view(args.front)
    top_all   = load_view(args.top)
    right_all = load_view(args.right)

    if not args.all_edges:
        front_all = [e for e in front_all if e.visible]
        top_all   = [e for e in top_all   if e.visible]
        right_all = [e for e in right_all if e.visible]

    print(f"  front: {len(front_all)} edges")
    print(f"  top  : {len(top_all)} edges")
    print(f"  right: {len(right_all)} edges")

    print("Annotating edges...")
    annotate(front_all)
    annotate(top_all)
    annotate(right_all)

    eps = compute_epsilon([front_all, top_all, right_all], args.eps)
    print(f"  ε = {eps:.4f}  (eps_t={args.eps})")

    _print_flag_summary("front", front_all)
    _print_flag_summary("top",   top_all)
    _print_flag_summary("right", right_all)

    print("Matching patterns...")
    raw = match_patterns(front_all, top_all, right_all, eps)
    edges_3d = deduplicate(raw, eps)
    print(f"  {len(raw)} raw matches → {len(edges_3d)} after deduplication")

    pattern_counts: dict[str, int] = {}
    for e in edges_3d:
        pattern_counts[e.pattern] = pattern_counts.get(e.pattern, 0) + 1
    for pat, cnt in sorted(pattern_counts.items()):
        print(f"    {pat}: {cnt}")

    out_path = Path(args.out)
    out_path.write_text(json.dumps(to_dict(edges_3d), indent=2), encoding="utf-8")
    print(f"Saved: {out_path}  ({len(edges_3d)} edges)")

    if args.viz:
        viz_path = out_path.with_suffix(".png")
        visualise(edges_3d, viz_path)


def _print_flag_summary(name: str, edges: list[Edge2D]) -> None:
    counts: dict[str, int] = {}
    for e in edges:
        counts[e.flag] = counts.get(e.flag, 0) + 1
    parts = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
    print(f"  {name}: {parts}")


if __name__ == "__main__":
    main()
