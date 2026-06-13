"""CadAgent: drawing image → CadQuery script → rendered model, with self-refinement.

Every run gets its own output directory.  Files written per run:

  out_dir/
    input.png              copy of the input drawing
    reasoning.md           Gemini's full step-by-step chain-of-thought
    feature_tree.json      Step 3 feature tree extracted from the reasoning
    model.py               final CadQuery script (from the successful attempt)
    model.step             exported STEP file
    model.stl              exported STL mesh
    model.html             interactive three.js 3D viewer
    model.svg              2D orthographic SVG projection
    summary.json           run metadata (attempts, success, timing, paths)

    # written for every FAILED attempt:
    attempt_1.py           script from attempt 1 (if it failed)
    attempt_1_error.txt    render / Python error from attempt 1
    attempt_2.py           script from attempt 2 (if it failed)
    attempt_2_error.txt
    …
"""

import json
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from backend.agent.prompts import format_refine_prompt, format_user_prompt, get_system_prompt
from backend.cad import RenderResult, render_file
from backend.llm import CodeResult, Conversation

_MAX_ERROR_CHARS = 2000
_JSON_BLOCK = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)


def _extract_json_block(text: str) -> list | dict | None:
    m = _JSON_BLOCK.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


@dataclass
class AgentRun:
    ok: bool
    out_dir: Path
    render: RenderResult
    attempts: int
    feature_tree: list | dict | None = field(default=None)

    def __bool__(self) -> bool:
        return self.ok


class CadAgent:
    def __init__(self, model: str | None = None, max_attempts: int = 3):
        self.max_attempts = max_attempts
        kwargs: dict = {"system_instruction": get_system_prompt(), "code_json": True}
        if model:
            kwargs["model"] = model
        self.chat = Conversation(**kwargs)

    def run(
        self,
        image_path: str | Path,
        out_dir: str | Path,
        params: dict | None = None,
    ) -> AgentRun:
        """Generate and render a CadQuery model for `image_path`.

        Args:
            image_path: Path to the drawing image (PNG, JPG, or PDF).
            out_dir:    Directory for all outputs (created if needed).
            params:     Optional authoritative dimension table.
        """
        image_path = Path(image_path)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        t_start = time.time()

        # ── Step 0: copy input ─────────────────────────────────────────────
        input_copy = out_dir / f"input{image_path.suffix}"
        if image_path.resolve() != input_copy.resolve():
            shutil.copy2(image_path, input_copy)
        print(f"[1/4] Input   → {input_copy}")

        # ── Step 1: first Gemini call ──────────────────────────────────────
        print("[2/4] Calling Gemini…")
        user_msg = format_user_prompt(params)
        result = self.chat.ask_code(user_msg, images=image_path)

        feature_tree = _extract_json_block(result.reasoning or "")

        # Save reasoning and feature tree immediately (before any render)
        self._save_reasoning(out_dir, result.reasoning or "", feature_tree)
        print(f"      reasoning → {out_dir / 'reasoning.md'}")
        if feature_tree is not None:
            print(f"      feature_tree → {out_dir / 'feature_tree.json'}")

        # ── Step 2–N: render + refine loop ─────────────────────────────────
        print("[3/4] Rendering…")
        render: RenderResult | None = None
        final_script: Path | None = None

        for attempt in range(1, self.max_attempts + 1):
            script = out_dir / "model.py"
            script.write_text(result.code, encoding="utf-8")

            render = render_file(
                script,
                out_dir=out_dir,
                name="model",
                formats=("step", "stl", "svg"),
            )

            if render.ok:
                print(f"      attempt {attempt}: OK")
                final_script = script
                break

            # Save the failing attempt before overwriting model.py next round
            attempt_script = out_dir / f"attempt_{attempt}.py"
            attempt_script.write_text(result.code, encoding="utf-8")
            err = render.stderr.strip()[-_MAX_ERROR_CHARS:]
            (out_dir / f"attempt_{attempt}_error.txt").write_text(err, encoding="utf-8")
            print(f"      attempt {attempt}: FAILED → {attempt_script.name}", file=sys.stderr)

            if attempt < self.max_attempts:
                result = self.chat.ask_code(format_refine_prompt(err))
                new_tree = _extract_json_block(result.reasoning or "")
                if new_tree:
                    feature_tree = new_tree
                    self._save_reasoning(out_dir, result.reasoning, feature_tree)

        ok = render is not None and render.ok

        # ── Step 3: summary ────────────────────────────────────────────────
        elapsed = round(time.time() - t_start, 1)
        outputs = {k: str(v) for k, v in (render.outputs if render else {}).items()}
        summary = {
            "ok": ok,
            "attempts": attempt,
            "elapsed_s": elapsed,
            "input": str(input_copy),
            "outputs": outputs,
        }
        (out_dir / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )

        if ok:
            print(f"[4/4] Outputs  → {out_dir}/")
            for fmt, path in outputs.items():
                print(f"      {fmt:6s} → {path}")
        else:
            print(f"[4/4] Failed after {attempt} attempt(s).", file=sys.stderr)

        return AgentRun(
            ok=ok,
            out_dir=out_dir,
            render=render or RenderResult(ok=False),
            attempts=attempt,
            feature_tree=feature_tree,
        )

    @staticmethod
    def _save_reasoning(
        out_dir: Path,
        reasoning: str,
        feature_tree: list | dict | None,
    ) -> None:
        (out_dir / "reasoning.md").write_text(reasoning, encoding="utf-8")
        if feature_tree is not None:
            (out_dir / "feature_tree.json").write_text(
                json.dumps(feature_tree, indent=2), encoding="utf-8"
            )
