"""CLI: `python -m backend.agent <drawing.png> [out_dir]` runs the CAD agent."""

import sys

from backend.agent.agent import CadAgent

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m backend.agent <drawing.png> [out_dir]", file=sys.stderr)
        raise SystemExit(2)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "renders"

    run = CadAgent().run(sys.argv[1], out_dir)
    print(f"run dir: {run.run_dir}")
    print(f"trace:   {run.trace_path}")
    if run.ok:
        print(f"visually verified: {run.verified}")
        if run.critique and not run.verified:
            print("remaining issues:", run.critique.issues)
        print("open:", run.run_dir / "final.html")
    else:
        print("failed to produce a rendering:", file=sys.stderr)
        print(run.render.stderr, file=sys.stderr, end="")
        raise SystemExit(1)
