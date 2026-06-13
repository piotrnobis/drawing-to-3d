"""CLI: `python -m backend.agent <drawing.png> [options]`

Every run creates a timestamped subdirectory under --out-base so intermediate
files from different runs never clobber each other:

  output/
    drawing_20260613_143022/
      input.png            copy of the input drawing
      reasoning.md         Gemini's step-by-step chain-of-thought
      feature_tree.json    Step 3 feature tree (dimensions + operations)
      model.py             final CadQuery script
      model.step           3D STEP file
      model.stl            3D mesh (STL)
      model.html           interactive 3D viewer (open in browser)
      model.svg            2D orthographic SVG
      summary.json         run metadata
      attempt_1.py         (only if attempt 1 failed)
      attempt_1_error.txt
      …
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from backend.agent.agent import CadAgent


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m backend.agent",
        description="Reconstruct a 3D CadQuery model from a 2D technical drawing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("drawing", metavar="drawing.png",
                        help="Path to the drawing image (PNG, JPG, or PDF)")
    parser.add_argument("--out-base", metavar="DIR", default="output",
                        help="Parent directory for run outputs (default: output/)")
    parser.add_argument("--out-dir", metavar="DIR",
                        help="Exact output directory (overrides --out-base + timestamp)")
    parser.add_argument("--params", metavar="params.json",
                        help="JSON dimension table — authoritative values injected "
                             "into the prompt (overrides reading dims from the image)")
    parser.add_argument("--model", metavar="model-id",
                        help="Gemini model ID override (e.g. gemini-2.5-pro)")
    parser.add_argument("--attempts", type=int, default=3, metavar="N",
                        help="Maximum self-refinement attempts (default: 3)")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    drawing = Path(args.drawing)
    if not drawing.exists():
        print(f"error: drawing not found: {drawing}", file=sys.stderr)
        raise SystemExit(2)

    # Output directory
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(args.out_base) / f"{drawing.stem}_{stamp}"

    # Optional dimension table
    params: dict | None = None
    if args.params:
        params_path = Path(args.params)
        if not params_path.exists():
            print(f"error: params file not found: {params_path}", file=sys.stderr)
            raise SystemExit(2)
        params = json.loads(params_path.read_text(encoding="utf-8"))
        print(f"params: loaded {len(params)} keys from {params_path}")

    print(f"run dir: {out_dir}/")
    print()

    agent = CadAgent(model=args.model, max_attempts=args.attempts)
    run = agent.run(drawing, out_dir=out_dir, params=params)

    if run.ok:
        html = run.render.outputs.get("html")
        if html:
            print()
            print(f"3D viewer: {html}")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
