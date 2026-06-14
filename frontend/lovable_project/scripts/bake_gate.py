"""Pre-bake the demo dimension-gate JSON from a real run's artifacts.

Reuses the actual backend gate logic (backend.agent.gate.evaluate) so the demo
table matches what the pipeline produced — no TS reimplementation. Run from the
repo root with the project env:

    python frontend/lovable_project/scripts/bake_gate.py renders/run_<ts>

Prints a JSON object: {summary, guess, rows[], nPass, nMeasured, verdict}.
"""

import json
import sys
from pathlib import Path

from backend.agent.gate import evaluate
from backend.agent.models import Analysis


def main() -> int:
    run_dir = Path(sys.argv[1])
    analysis = Analysis.model_validate_json(
        (run_dir / "analysis.json").read_text(encoding="utf-8")
    )
    measurements = json.loads((run_dir / "final.measurements.json").read_text(encoding="utf-8"))
    gate = evaluate(analysis.dimensions, measurements)
    out = {
        "summary": analysis.summary,
        "guess": analysis.guess,
        "rows": [
            {
                "label": r.label,
                "kind": r.kind,
                "target": r.target,
                "tol": r.tol,
                "measured": r.measured,
                "status": r.status,
            }
            for r in gate.rows
        ],
        "nPass": gate.n_pass,
        "nMeasured": gate.n_measured,
        "verdict": gate.verdict(),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
