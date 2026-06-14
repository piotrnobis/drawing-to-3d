"""Dimensional gate: check the measured B-rep against the analysis dimension table.

This is the hard size signal — an objective pass/fail per dimension. It only
checks the kinds we can currently measure (overall bbox, hole diameters/count);
others are reported as `unmeasured` and never fail the gate.
"""

from dataclasses import dataclass, field

from backend.agent.models import Dimension

_DEFAULT_TOL = 0.5  # mm, when a dimension carries no usable tolerance


@dataclass
class GateRow:
    label: str
    kind: str
    target: float
    tol: float
    measured: float | None
    status: str  # "pass" | "fail" | "unmeasured"


@dataclass
class GateResult:
    rows: list[GateRow] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """No failing rows. Unmeasured rows don't block (we can't verify them)."""
        return not any(r.status == "fail" for r in self.rows)

    @property
    def n_pass(self) -> int:
        return sum(1 for r in self.rows if r.status == "pass")

    def table(self) -> str:
        if not self.rows:
            return "(no dimensions to check)"
        lines = [
            "| dimension | kind | target | measured | status |",
            "|---|---|---|---|---|",
        ]
        for r in self.rows:
            measured = "—" if r.measured is None else f"{r.measured:g}"
            lines.append(
                f"| {r.label} | {r.kind} | {r.target:g} ±{r.tol:g} | {measured} | {r.status} |"
            )
        return "\n".join(lines)

    def failures(self) -> str:
        """Failing rows as feedback text for the refine step."""
        return "\n".join(
            f"- {r.label}: expected {r.target:g} ±{r.tol:g} mm but measured {r.measured:g} mm"
            for r in self.rows
            if r.status == "fail"
        )


def _take_nearest(pool: list[float], value: float) -> float | None:
    """Pop and return the pool entry nearest `value` (so each callout matches one feature)."""
    if not pool:
        return None
    best = min(pool, key=lambda x: abs(x - value))
    pool.remove(best)
    return best


def evaluate(dimensions: list[Dimension], measurements: dict) -> GateResult:
    """Compare each analysis dimension to the measured B-rep."""
    bbox = measurements.get("bbox", {})
    remaining_holes = sorted(measurements.get("hole_diameters", []))

    # Per-pattern hole geometry -> consumable pools for count / pitch / bolt-circle.
    groups = measurements.get("hole_groups", [])
    counts = [float(g["count"]) for g in groups]
    pitches = [g["pitch"] for g in groups if g.get("pitch") is not None]
    pcds = [g["pcd"] for g in groups if g.get("pcd") is not None]

    # The overall extent along an axis is a SINGLE dimension (the largest one
    # tagged to that axis). Smaller dims mistagged as bbox_* are sub-features the
    # model labelled wrong; we can't verify those here, so leave them unmeasured.
    axis_key = {"bbox_x": "x", "bbox_y": "y", "bbox_z": "z"}
    is_overall: set[int] = set()
    for kind in axis_key:
        same_axis = [d for d in dimensions if d.kind == kind]
        if same_axis:
            is_overall.add(id(max(same_axis, key=lambda d: d.value)))

    rows: list[GateRow] = []
    for dim in dimensions:
        tol = dim.tolerance if dim.tolerance and dim.tolerance > 0 else _DEFAULT_TOL
        measured: float | None = None

        if dim.kind in axis_key and id(dim) in is_overall:
            measured = bbox.get(axis_key[dim.kind])
        elif dim.kind == "hole_diameter":
            measured = _take_nearest(remaining_holes, dim.value)
        elif dim.kind == "hole_count":
            measured = _take_nearest(counts, dim.value)
        elif dim.kind == "hole_pitch":
            measured = _take_nearest(pitches, dim.value)
        elif dim.kind == "bolt_circle":
            measured = _take_nearest(pcds, dim.value)
        # spacing / thickness / other: not auto-measured -> unmeasured

        if measured is None:
            status = "unmeasured"
        else:
            status = "pass" if abs(measured - dim.value) <= tol else "fail"
        rows.append(GateRow(dim.label, dim.kind, dim.value, tol, measured, status))

    return GateResult(rows)
