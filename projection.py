"""
projection.py — Orthographic projections from a STEP file with Hidden Line Removal.

Reads a STEP (.stp/.step) file, generates standard engineering views, and saves
each projection as a PNG/SVG image. Visible edges are drawn as solid black lines;
hidden (occluded) edges as dashed gray lines.

View directions
---------------
Five standard views are generated using the six principal axes:

  View    Viewer at   N (toward viewer)   Vx (image right)   Image up
  ------  ----------  ------------------  -----------------  --------
  front   -Y          (0, -1,  0)         ( 1,  0,  0)       +Z world
  top      +Z         (0,  0,  1)         ( 1,  0,  0)       +Y world
  right   +X          (1,  0,  0)         ( 0,  1,  0)       +Z world
  left    -X          (-1, 0,  0)         ( 0, -1,  0)       +Z world
  iso     (1,1,1)     (1,1,1)/√3          (1,-1,0)/√2        —

The Vx vectors are chosen so N × Vx = (0,0,1) for all orthographic views,
meaning +Z in world is always "up" in the image with no manual flipping.

Hidden Line Removal
-------------------
HLRBRep_Algo (exact BREP algorithm) classifies each edge segment as visible
or hidden by comparing it against every face in the model:
  • Visible: no face lies between the edge segment and the viewer.
  • Hidden: at least one face occludes the edge segment.
  • Silhouette/outline edges (boundary between front-facing and back-facing
    faces) are always visible and extracted separately as outline edges.

Usage
-----
  python projection.py <file.stp> [--output-dir DIR] [--views VIEWS]
                                  [--format png|svg] [--dpi N] [--samples N]

  python projection.py examples/Part1.stp
  python projection.py examples/blower.stp --output-dir output/ --dpi 200
  python projection.py examples/Part1.stp --views front,top,right
"""

import argparse
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend — must precede pyplot import
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GeomAbs import GeomAbs_Line
from OCC.Core.gp import gp_Ax2, gp_Dir, gp_Pnt
from OCC.Core.HLRAlgo import HLRAlgo_Projector
from OCC.Core.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Standard import Standard_Failure
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopAbs import TopAbs_EDGE
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopoDS import topods


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ViewDef:
    name: str
    N: tuple   # unit vector pointing FROM scene TOWARD viewer
    Vx: tuple  # unit horizontal-right vector in the projected image


@dataclass
class ViewEdges:
    visible: list = field(default_factory=list)  # list of [(x,y), ...]
    hidden: list = field(default_factory=list)   # list of [(x,y), ...]


# ---------------------------------------------------------------------------
# View definitions
# ---------------------------------------------------------------------------

_S3 = 1.0 / math.sqrt(3.0)
_S2 = 1.0 / math.sqrt(2.0)

VIEWS: dict = {
    "front": ViewDef("front", N=(0.0, -1.0, 0.0), Vx=(1.0,  0.0, 0.0)),
    "top":   ViewDef("top",   N=(0.0,  0.0, 1.0), Vx=(1.0,  0.0, 0.0)),
    "right": ViewDef("right", N=(1.0,  0.0, 0.0), Vx=(0.0,  1.0, 0.0)),
    "left":  ViewDef("left",  N=(-1.0, 0.0, 0.0), Vx=(0.0, -1.0, 0.0)),
    "iso":   ViewDef("iso",   N=(_S3,  _S3,  _S3), Vx=(_S2, -_S2, 0.0)),
}

# Combined layout: 2×2 grid using third-angle ANSI convention
COMBINED_LAYOUT = [
    ["top",   "iso"],
    ["front", "right"],
]

VIEW_LABELS = {
    "front": "Front View",
    "top":   "Top View",
    "right": "Right Side View",
    "left":  "Left Side View",
    "iso":   "Isometric View",
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate orthographic projections with HLR from a STEP file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("step_file", help="Path to the .stp / .step file")
    parser.add_argument(
        "--output-dir", default=".", metavar="DIR",
        help="Directory to write output images (default: current directory)",
    )
    parser.add_argument(
        "--views", default=",".join(VIEWS.keys()), metavar="VIEWS",
        help=f"Comma-separated list of views (default: all). "
             f"Available: {', '.join(VIEWS.keys())}",
    )
    parser.add_argument(
        "--format", choices=["png", "svg"], default="png",
        help="Output image format (default: png)",
    )
    parser.add_argument(
        "--dpi", type=int, default=150,
        help="Resolution for PNG output (default: 150)",
    )
    parser.add_argument(
        "--samples", type=int, default=50,
        help="Sample points per non-linear curve segment (default: 50)",
    )
    args = parser.parse_args()

    # Validate STEP file
    step_path = Path(args.step_file)
    if not step_path.exists():
        parser.error(f"File not found: {args.step_file}")
    if step_path.suffix.lower() not in (".stp", ".step"):
        print(f"Warning: '{args.step_file}' does not have a .stp/.step extension.")

    # Parse and validate view names
    requested = [v.strip().lower() for v in args.views.split(",") if v.strip()]
    invalid = [v for v in requested if v not in VIEWS]
    if invalid:
        parser.error(f"Unknown view(s): {', '.join(invalid)}. "
                     f"Valid: {', '.join(VIEWS.keys())}")
    if not requested:
        parser.error("--views must include at least one view name.")
    args.views_list = requested

    # Create output directory
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    args.output_path = out

    return args


# ---------------------------------------------------------------------------
# STEP loading
# ---------------------------------------------------------------------------

def load_step(filepath: str):
    """Load a STEP file and return a single merged TopoDS_Shape."""
    print(f"[1/3] Loading STEP file: {filepath}")
    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)
    if status != IFSelect_RetDone:
        raise ValueError(
            f"STEPControl_Reader failed (status {status}): {filepath}\n"
            f"Ensure the file is a valid STEP/STP file."
        )
    reader.TransferRoots()
    shape = reader.OneShape()
    if shape.IsNull():
        raise ValueError(
            f"STEP file transferred but produced an empty shape: {filepath}"
        )
    print("    Shape loaded successfully.")
    return shape


# ---------------------------------------------------------------------------
# HLR computation
# ---------------------------------------------------------------------------

def compute_hlr(shape, view_def: ViewDef):
    """Run Hidden Line Removal for one view. Returns HLRBRep_HLRToShape."""
    ax2 = gp_Ax2(
        gp_Pnt(0.0, 0.0, 0.0),
        gp_Dir(*view_def.N),
        gp_Dir(*view_def.Vx),
    )
    projector = HLRAlgo_Projector(ax2)
    hlr = HLRBRep_Algo()
    hlr.Add(shape)
    hlr.Projector(projector)
    try:
        hlr.Update()
        hlr.Hide()
    except Standard_Failure as exc:
        raise RuntimeError(
            f"HLR computation failed for view '{view_def.name}': {exc}"
        ) from exc
    return HLRBRep_HLRToShape(hlr)


# ---------------------------------------------------------------------------
# Edge extraction
# ---------------------------------------------------------------------------

def extract_polylines(compound, n_pts: int = 50) -> list:
    """
    Discretize all edges in a TopoDS compound into (x, y) polylines.

    HLR projects edge geometry onto the view plane. The X and Y components
    of each sampled point are the 2D image coordinates; Z (depth) is discarded.
    """
    if compound is None or compound.IsNull():
        return []

    polylines = []
    explorer = TopExp_Explorer(compound, TopAbs_EDGE)
    while explorer.More():
        edge = topods.Edge(explorer.Current())

        # Degenerate edges collapse to a vertex — skip to avoid crashes
        if BRep_Tool.Degenerated(edge):
            explorer.Next()
            continue

        try:
            curve = BRepAdaptor_Curve(edge)
            first = curve.FirstParameter()
            last = curve.LastParameter()

            if abs(last - first) < 1e-10:
                explorer.Next()
                continue

            # Lines need only 2 points; curves need more for smooth rendering
            count = 2 if curve.GetType() == GeomAbs_Line else n_pts

            pts = []
            for i in range(count):
                t = first + (last - first) * i / (count - 1)
                p = curve.Value(t)
                pts.append((p.X(), p.Y()))

            if len(pts) >= 2:
                polylines.append(pts)

        except (Standard_Failure, RuntimeError):
            pass  # skip malformed edges

        explorer.Next()

    return polylines


def extract_edges(hlr_shape, n_pts: int = 50) -> ViewEdges:
    """Collect visible and hidden polylines from a HLRBRep_HLRToShape."""
    visible = (
        extract_polylines(hlr_shape.VCompound(), n_pts)
        + extract_polylines(hlr_shape.OutLineVCompound(), n_pts)
    )
    hidden = (
        extract_polylines(hlr_shape.HCompound(), n_pts)
        + extract_polylines(hlr_shape.OutLineHCompound(), n_pts)
    )
    return ViewEdges(visible=visible, hidden=hidden)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_view(edges: ViewEdges, title: str, ax: Axes) -> None:
    """
    Draw one view onto a matplotlib Axes.

    Hidden edges are drawn first (painter's algorithm) so solid visible lines
    appear on top at intersections, matching engineering drawing convention.
    """
    # Hidden edges: dashed gray
    for polyline in edges.hidden:
        if len(polyline) < 2:
            continue
        xs, ys = zip(*polyline)
        ax.plot(xs, ys, color="#888888", linewidth=0.5, linestyle="--",
                solid_capstyle="butt")

    # Visible edges: solid black
    for polyline in edges.visible:
        if len(polyline) < 2:
            continue
        xs, ys = zip(*polyline)
        ax.plot(xs, ys, color="black", linewidth=1.0, linestyle="-",
                solid_capstyle="projecting")

    # Compute bounds with 10% padding
    all_pts = [pt for pl in edges.visible + edges.hidden for pt in pl]
    if all_pts:
        xs_all = [p[0] for p in all_pts]
        ys_all = [p[1] for p in all_pts]
        xspan = max(xs_all) - min(xs_all) or 1.0
        yspan = max(ys_all) - min(ys_all) or 1.0
        pad = max(xspan, yspan) * 0.10
        ax.set_xlim(min(xs_all) - pad, max(xs_all) + pad)
        ax.set_ylim(min(ys_all) - pad, max(ys_all) + pad)
    else:
        ax.set_xlim(-1.0, 1.0)
        ax.set_ylim(-1.0, 1.0)

    ax.set_aspect("equal", adjustable="box")
    ax.set_facecolor("white")
    ax.axis("off")
    ax.set_title(title, fontsize=10, pad=4)


def save_view(edges: ViewEdges, title: str, filepath: Path,
              fmt: str, dpi: int) -> None:
    """Save a single view to file."""
    fig, ax = plt.subplots(1, 1, figsize=(8, 8), facecolor="white")
    render_view(edges, title, ax)
    fig.tight_layout()
    fig.savefig(filepath, format=fmt, dpi=dpi, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


def save_combined(views_edges: dict, layout: list, filepath: Path,
                  fmt: str, dpi: int) -> None:
    """
    Save a multi-view layout to a single file.

    layout is a 2D list of view names (or None for blank cells):
        [["top", "iso"],
         ["front", "right"]]
    """
    nrows = len(layout)
    ncols = max(len(row) for row in layout)
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(8 * ncols, 8 * nrows),
                             facecolor="white")

    # Normalise axes to a 2D list regardless of shape
    if nrows == 1 and ncols == 1:
        axes_2d = [[axes]]
    elif nrows == 1:
        axes_2d = [list(axes)]
    elif ncols == 1:
        axes_2d = [[ax] for ax in axes]
    else:
        axes_2d = [list(row) for row in axes]

    for r, row in enumerate(layout):
        for c, view_name in enumerate(row):
            ax = axes_2d[r][c]
            if view_name is None or view_name not in views_edges:
                ax.axis("off")
            else:
                render_view(views_edges[view_name],
                            VIEW_LABELS.get(view_name, view_name.capitalize()),
                            ax)

    fig.suptitle("Orthographic Projections", fontsize=14, y=1.01)
    fig.tight_layout()
    fig.savefig(filepath, format=fmt, dpi=dpi, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    step_path = Path(args.step_file).resolve()
    stem = step_path.stem
    fmt = args.format
    dpi = args.dpi
    n_pts = args.samples
    requested_views = args.views_list
    out_dir = args.output_path

    # Load
    shape = load_step(str(step_path))

    # Per-view HLR projection
    print(f"[2/3] Computing HLR projections for {len(requested_views)} view(s)...")
    views_edges: dict = {}

    for i, view_name in enumerate(requested_views, 1):
        view_def = VIEWS[view_name]
        print(f"  [{i}/{len(requested_views)}] {view_name}...", end=" ", flush=True)

        hlr_shape = compute_hlr(shape, view_def)
        edges = extract_edges(hlr_shape, n_pts)

        n_vis = len(edges.visible)
        n_hid = len(edges.hidden)
        print(f"done  ({n_vis} visible, {n_hid} hidden polylines)")

        views_edges[view_name] = edges

        out_file = out_dir / f"{stem}_{view_name}.{fmt}"
        save_view(edges, VIEW_LABELS.get(view_name, view_name.capitalize()),
                  out_file, fmt, dpi)
        print(f"    Saved: {out_file}")

    # Combined layout
    print("[3/3] Generating combined layout...")
    filtered_layout = [
        [v if v in views_edges else None for v in row]
        for row in COMBINED_LAYOUT
    ]
    n_in_layout = sum(
        1 for row in filtered_layout for v in row if v is not None
    )

    if n_in_layout >= 2:
        combined_path = out_dir / f"{stem}_combined.{fmt}"
        save_combined(views_edges, filtered_layout, combined_path, fmt, dpi)
        print(f"    Saved: {combined_path}")
    else:
        print("    Skipped combined layout (fewer than 2 requested views fit the grid).")

    print("Done.")


if __name__ == "__main__":
    main()
