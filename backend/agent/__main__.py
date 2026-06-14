"""CLI: `python -m backend.agent <drawing.png> [out_dir] [--thinking LEVEL]`."""

import argparse

from backend.agent.agent import CadAgent
from backend.llm.gemini import THINKING_BUDGETS

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct a CadQuery model from a drawing.")
    parser.add_argument("drawing", help="path to the engineering drawing image")
    parser.add_argument("out_dir", nargs="?", default="renders", help="output base dir")
    parser.add_argument(
        "--thinking",
        choices=list(THINKING_BUDGETS),
        default=None,
        help="model thinking level (default: model's own)",
    )
    parser.add_argument(
        "--staged",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="force staged feature-by-feature build on/off (default: auto by complexity)",
    )
    args = parser.parse_args()

    run = CadAgent(thinking=args.thinking, staged=args.staged).run(args.drawing, args.out_dir)
    print(f"run dir: {run.run_dir}")
    print(f"trace:   {run.trace_path}")
    if run.ok:
        print(f"verified (visual + dimensions): {run.verified}")
        if run.gate and run.gate.rows:
            print("dimension gate:")
            print(run.gate.table())
        if run.critique and not run.critique.matches:
            print("remaining visual issues:", run.critique.issues)
        print("open:", run.run_dir / "final.html")
    else:
        print("failed to produce a rendering")
        raise SystemExit(1)
