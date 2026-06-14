"""Sandbox harness: runs INSIDE the subprocess spawned by render.py.

It execs an untrusted CadQuery script, resolves the model object, exports it to
the requested formats, measures the B-rep, and renders multi-view PNG snapshots.
This file is the only place a CadQuery script is ever executed, and it only runs
in the isolated subprocess — never imported by the app. Do not import application
code here.

Usage (invoked by render.py, not by hand):
    python _harness.py <script_path> <out_dir> <name> <formats_csv>
"""

import json
import math
import sys
import traceback
from pathlib import Path

EXPORT_TYPES = {
    ".step": "STEP",
    ".stp": "STEP",
    ".stl": "STL",
    ".svg": "SVG",
}

# Cylinders spanning nearly a full turn are holes/bores; partial cylinders
# (~90deg) are fillets/rounds and must not be reported as holes.
_FULL_TURN = 2 * math.pi
_HOLE_SPAN_MIN = 5.0  # rad (~286deg); a fillet is ~pi/2

# (camera direction from focal point, view-up) per view. Parallel projection.
_VIEWS = {
    "front": ((0, -1, 0), (0, 0, 1)),
    "top": ((0, 0, 1), (0, 1, 0)),
    "side": ((1, 0, 0), (0, 0, 1)),
    "iso": ((1, -1, 0.8), (0, 0, 1)),
}


def _resolve_object(namespace, shown):
    """Pick the model to export: an explicit `result`, else the last show_object()."""
    obj = namespace.get("result")
    if obj is not None:
        return obj
    if shown:
        return shown[-1]
    raise RuntimeError(
        "Script produced no model. Assign the model to a variable named "
        "`result`, or call show_object(model)."
    )


def _as_shape(model):
    """Normalize a Workplane or Shape to a Shape."""
    return model.val() if hasattr(model, "val") else model


def _center_on_origin(model):
    """Translate the model so its bounding-box center sits at the world origin.

    The model writes geometry wherever was convenient; for a tidy export we want the
    coordinate origin at the center of the part's overall envelope. This is purely a
    rigid translation, so every measurement we take (bbox lengths, hole pitch/PCD —
    all relative) is unchanged; only the absolute placement moves. Works on a
    Workplane or a bare Shape (both expose `.translate`).
    """
    bb = _as_shape(model).BoundingBox()
    offset = (
        -(bb.xmin + bb.xmax) / 2,
        -(bb.ymin + bb.ymax) / 2,
        -(bb.zmin + bb.zmax) / 2,
    )
    if all(abs(c) < 1e-6 for c in offset):  # already centered
        return model
    return model.translate(offset)


def _measure(shape) -> dict:
    """Measure the B-rep: overall bounding box and hole diameters.

    Holes are near-full cylindrical faces; fillets (partial cylinders) are
    excluded by their angular span.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepTools import BRepTools

    bb = shape.BoundingBox()
    holes = []  # raw per-hole geometry, grouped below into patterns
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        umin, umax, _, _ = BRepTools.UVBounds_s(face.wrapped)
        if (umax - umin) < _HOLE_SPAN_MIN:
            continue  # fillet/round, not a hole
        cyl = BRepAdaptor_Surface(face.wrapped).Cylinder()
        dia = round(cyl.Radius() * 2, 3)
        d = cyl.Axis().Direction()
        axis = (d.X(), d.Y(), d.Z())
        # dominant axis component, sign-normalized so opposite-pointing holes group
        i = max(range(3), key=lambda k: abs(axis[k]))
        sign = 1.0 if axis[i] >= 0 else -1.0
        canon = tuple(round(c * sign, 2) for c in axis)
        fbb = face.BoundingBox()
        mins = (fbb.xmin, fbb.ymin, fbb.zmin)
        maxs = (fbb.xmax, fbb.ymax, fbb.zmax)
        center = tuple((lo + hi) / 2 for lo, hi in zip(mins, maxs))
        perp = [j for j in range(3) if j != i]  # the two in-pattern axes
        holes.append(
            {
                "dia": dia,
                # holes of one pattern share axis, diameter, and the face's along-axis span
                "key": (canon, dia, round(mins[i]), round(maxs[i])),
                "center": (center[perp[0]], center[perp[1]]),
            }
        )

    return {
        "bbox": {"x": round(bb.xlen, 3), "y": round(bb.ylen, 3), "z": round(bb.zlen, 3)},
        "hole_diameters": sorted(h["dia"] for h in holes),
        "hole_count": len(holes),
        "hole_groups": _group_holes(holes),
        "solid_count": len(shape.Solids()),  # >1 means disconnected pieces
    }


def _group_holes(holes: list[dict]) -> list[dict]:
    """Cluster holes into patterns and measure each: count, diameter, pitch, PCD."""
    by_key: dict = {}
    for h in holes:
        by_key.setdefault(h["key"], []).append(h["center"])

    groups = []
    for (_axis, dia, _lo, _hi), centers in by_key.items():
        n = len(centers)
        pitch = pcd = None
        if n > 1:
            cx = sum(p[0] for p in centers) / n
            cy = sum(p[1] for p in centers) / n
            pcd = round(2 * sum(math.hypot(p[0] - cx, p[1] - cy) for p in centers) / n, 3)
            pitch = round(
                min(
                    math.hypot(a[0] - b[0], a[1] - b[1])
                    for idx, a in enumerate(centers)
                    for b in centers[idx + 1 :]
                ),
                3,
            )
        groups.append({"count": n, "diameter": dia, "pitch": pitch, "pcd": pcd})

    groups.sort(key=lambda g: (-g["count"], g["diameter"]))
    return groups


def _render_views(shape, out: Path, name: str, tol: float = 0.1) -> list[str]:
    """Render orthographic + isometric PNG snapshots via headless vtk."""
    import vtk

    verts, tris = shape.tessellate(tol)
    points = vtk.vtkPoints()
    for v in verts:
        points.InsertNextPoint(v.x, v.y, v.z)
    cells = vtk.vtkCellArray()
    for tri in tris:
        cells.InsertNextCell(3)
        for idx in tri:
            cells.InsertCellPoint(idx)
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(cells)

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(poly)
    normals.SetFeatureAngle(30)  # split shading at real creases, keep curves smooth
    normals.Update()

    # Surface: a neutral matte "clay" gray. Saturated colors compress the shading
    # gradient and hide concave cuts; gray + low specular keeps form readable.
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(0.72, 0.72, 0.72)
    prop.SetInterpolationToPhong()
    prop.SetAmbient(0.28)  # lift shadowed pockets out of pure black
    prop.SetDiffuse(0.75)
    prop.SetSpecular(0.12)  # a hint of highlight, not glare
    prop.SetSpecularPower(20)

    # Feature edges: the single biggest legibility win. Draw real geometric edges
    # (cut boundaries, hole rims, silhouettes) as dark lines so every cut is obvious.
    edges = vtk.vtkFeatureEdges()
    edges.SetInputData(poly)
    edges.BoundaryEdgesOn()
    edges.FeatureEdgesOn()
    edges.SetFeatureAngle(30)  # only sharp creases; ignores tessellation facets on curves
    edges.ManifoldEdgesOff()
    edges.NonManifoldEdgesOff()
    edge_mapper = vtk.vtkPolyDataMapper()
    edge_mapper.SetInputConnection(edges.GetOutputPort())
    edge_mapper.ScalarVisibilityOff()
    edge_mapper.SetResolveCoincidentTopologyToPolygonOffset()  # keep lines above the surface
    edge_actor = vtk.vtkActor()
    edge_actor.SetMapper(edge_mapper)
    edge_actor.GetProperty().SetColor(0.12, 0.12, 0.12)
    edge_actor.GetProperty().SetLineWidth(1.5)
    edge_actor.GetProperty().SetLighting(False)

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.AddActor(edge_actor)
    renderer.SetBackground(1, 1, 1)
    # Multi-directional lighting (key + fill + back + head), camera-relative so it
    # re-lights from each view — gives the varied shadow directions that reveal depth.
    light_kit = vtk.vtkLightKit()
    light_kit.SetKeyToFillRatio(2.5)
    light_kit.SetKeyToBackRatio(3.0)
    light_kit.AddLightsToRenderer(renderer)
    camera = renderer.GetActiveCamera()
    camera.ParallelProjectionOn()

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.AddRenderer(renderer)
    window.SetSize(640, 640)

    written = []
    for view, (direction, up) in _VIEWS.items():
        camera.SetFocalPoint(0, 0, 0)
        camera.SetPosition(*direction)
        camera.SetViewUp(*up)
        renderer.ResetCamera()
        window.Render()
        grab = vtk.vtkWindowToImageFilter()
        grab.SetInput(window)
        grab.Update()
        target = out / f"{name}.{view}.png"
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(str(target))
        writer.SetInputConnection(grab.GetOutputPort())
        writer.Write()
        written.append(str(target))
    return written


def main() -> int:
    script_path, out_dir, name, formats_csv = sys.argv[1:5]
    formats = [f.strip().lower() for f in formats_csv.split(",") if f.strip()]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    import cadquery as cq
    from cadquery import exporters

    shown = []

    def show_object(obj, *args, **kwargs):  # cq-editor compatible stub
        shown.append(obj)

    namespace = {
        "__name__": "__cadquery_script__",
        "cq": cq,
        "show_object": show_object,
        "log": lambda *a, **k: None,
    }

    code = Path(script_path).read_text(encoding="utf-8")
    exec(compile(code, script_path, "exec"), namespace)  # noqa: S102 — sandboxed subprocess

    model = _resolve_object(namespace, shown)
    model = _center_on_origin(model)
    shape = _as_shape(model)

    written = []
    for fmt in formats:
        ext = fmt if fmt.startswith(".") else f".{fmt}"
        export_type = EXPORT_TYPES.get(ext)
        if export_type is None:
            print(f"skip: unsupported format {fmt!r}", file=sys.stderr)
            continue
        target = out / f"{name}{ext}"
        exporters.export(model, str(target), exportType=export_type)
        written.append(str(target))

    # Auxiliary outputs — never fatal to the export step.
    try:
        measurements = _measure(shape)
        meas_path = out / f"{name}.measurements.json"
        meas_path.write_text(json.dumps(measurements, indent=2), encoding="utf-8")
        written.append(str(meas_path))
    except Exception:
        print("warning: measurement failed", file=sys.stderr)
        traceback.print_exc()

    try:
        written.extend(_render_views(shape, out, name))
    except Exception:
        print("warning: view rendering failed", file=sys.stderr)
        traceback.print_exc()

    for path in written:
        print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
