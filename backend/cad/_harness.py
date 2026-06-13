"""Sandbox harness: runs INSIDE the subprocess spawned by render.py.

It execs an untrusted CadQuery script, resolves the model object, and exports
it to the requested formats. This file is the only place a CadQuery script is
ever executed, and it only runs in the isolated subprocess — never imported by
the app. Do not import application code here.

Usage (invoked by render.py, not by hand):
    python _harness.py <script_path> <out_dir> <name> <formats_csv>
"""

import sys
import traceback
from pathlib import Path

EXPORT_TYPES = {
    ".step": "STEP",
    ".stp": "STEP",
    ".stl": "STL",
    ".svg": "SVG",
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

    for path in written:
        print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
