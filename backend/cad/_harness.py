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


def _measure(shape) -> dict:
    """Measure the B-rep: overall bounding box and hole diameters.

    Holes are near-full cylindrical faces; fillets (partial cylinders) are
    excluded by their angular span.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepTools import BRepTools

    bb = shape.BoundingBox()
    holes = []
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        umin, umax, _, _ = BRepTools.UVBounds_s(face.wrapped)
        if (umax - umin) < _HOLE_SPAN_MIN:
            continue  # fillet/round, not a hole
        radius = BRepAdaptor_Surface(face.wrapped).Cylinder().Radius()
        holes.append(round(radius * 2, 3))

    return {
        "bbox": {"x": round(bb.xlen, 3), "y": round(bb.ylen, 3), "z": round(bb.zlen, 3)},
        "hole_diameters": sorted(holes),
        "hole_count": len(holes),
        "solid_count": len(shape.Solids()),  # >1 means disconnected pieces
    }


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
    normals.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.30, 0.55, 0.96)

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(1, 1, 1)
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
