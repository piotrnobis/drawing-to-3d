"""CLI: `python -m backend.agent <drawing.png> [out.py]` runs the CAD agent."""

import sys

from backend.agent.agent import CadAgent

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m backend.agent <drawing.png> [out.py]", file=sys.stderr)
        raise SystemExit(2)
    out = sys.argv[2] if len(sys.argv) > 2 else "generated.py"

    run = CadAgent().run(sys.argv[1], out)
    if run.ok:
        print(f"visually verified: {run.verified}")
        if run.critique and not run.verified:
            print("remaining issues:", run.critique.issues)
        print("outputs ->", {k: str(v) for k, v in run.render.outputs.items()})
        print("open:", run.render.outputs.get("html"))
        print("trace:", run.trace_path)
    else:
        print("failed to produce a rendering:", file=sys.stderr)
        print(run.render.stderr, file=sys.stderr, end="")
        raise SystemExit(1)
