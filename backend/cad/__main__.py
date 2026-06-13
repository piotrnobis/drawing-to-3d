"""CLI: `python -m backend.cad <script.py> [out_dir]` renders a CadQuery script."""

import sys

from backend.cad.render import render_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m backend.cad <script.py> [out_dir]", file=sys.stderr)
        raise SystemExit(2)
    out = sys.argv[2] if len(sys.argv) > 2 else "renders"
    result = render_file(sys.argv[1], out_dir=out)
    if result.stdout:
        print(result.stdout, end="")
    if result.ok:
        print("OK ->", {k: str(v) for k, v in result.outputs.items()})
        if result.measurements:
            print("measurements ->", result.measurements)
    else:
        print("FAILED", file=sys.stderr)
        print(result.stderr, file=sys.stderr, end="")
        raise SystemExit(1)
