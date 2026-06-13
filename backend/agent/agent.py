"""The CAD agent: drawing -> CadQuery -> render -> visual self-critique -> refine.

`CadAgent` holds one Gemini `Conversation` (persistent system prompt + CadQuery
reference). Each run:
  1. generates a script and renders it, repairing on code errors (inner loop);
  2. shows Gemini the original drawing alongside the model's rendered views and
     asks whether they match (visual critique);
  3. if they don't, feeds the discrepancies back and regenerates (outer loop),
     bounded by `max_refine`.
Everything happens in the SAME conversation, so each step carries full context.

Every run also writes a `<out>.trace.md` capturing the model's reasoning, render
attempts/errors, and critiques — so you can follow its thinking and tune prompts.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

from google.genai import types

from backend.agent.prompts import (
    REFINE_PROMPT,
    SYSTEM_PROMPT,
    USER_PROMPT,
    VISUAL_CRITIQUE_PROMPT,
    VISUAL_REFINE_PROMPT,
)
from backend.cad import RenderResult, render_file
from backend.llm import CodeResult, Conversation

# Tracebacks can be long; the actionable part is the tail. Keep tokens sane.
_MAX_ERROR_CHARS = 2000
_REASONING_PREVIEW_CHARS = 240

_VIEW_KEYS = ("view_front", "view_top", "view_side", "view_iso")

# Critique turn: list discrepancies first, then decide (reason-before-verdict).
_CRITIQUE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "issues": types.Schema(
            type=types.Type.STRING,
            description="Concrete discrepancies between the model and the drawing; empty if none.",
        ),
        "matches": types.Schema(
            type=types.Type.BOOLEAN,
            description="True only if the model is a faithful reconstruction of the drawing.",
        ),
    },
    required=["issues", "matches"],
    property_ordering=["issues", "matches"],
)


@dataclass
class CritiqueResult:
    matches: bool
    issues: str


@dataclass
class AgentRun:
    ok: bool  # a model rendered successfully
    verified: bool  # passed the visual critique
    script: Path
    render: RenderResult
    critique: CritiqueResult | None = None
    refines: int = 0
    trace_path: Path | None = None

    def __bool__(self) -> bool:
        return self.ok


class CadAgent:
    def __init__(self, model: str | None = None, max_repair: int = 3, max_refine: int = 2):
        self.max_repair = max_repair  # code-error retries per generation
        self.max_refine = max_refine  # visual-mismatch retries
        kwargs = {"system_instruction": SYSTEM_PROMPT}
        if model:
            kwargs["model"] = model
        self.chat = Conversation(**kwargs)
        self._trace: list[str] = []
        self._trace_path: Path | None = None

    def run(self, image_path: str | Path, out_path: str | Path = "generated.py") -> AgentRun:
        """Generate, render, and visually refine a CadQuery model for `image_path`."""
        out_path = Path(out_path)
        self._trace = []
        self._trace_path = out_path.with_suffix(".trace.md")
        self._record(f"# Agent trace — {image_path}\n")
        print(f"trace -> {self._trace_path}")

        code = self.chat.ask_code(USER_PROMPT, images=image_path)
        self._record_generation("Initial generation", code)

        script, render = self._render_with_repair(code, out_path)
        if not render.ok:
            self._record("\n**Stopped: could not produce a rendering.**")
            return AgentRun(False, False, script, render, trace_path=self._trace_path)

        critique: CritiqueResult | None = None
        for refine in range(self.max_refine + 1):
            critique = self._critique(image_path, render)
            self._record(
                f"\n## Critique {refine} — match: {critique.matches}\n\n"
                f"{critique.issues or '(no issues reported)'}"
            )
            print(f"refine {refine}: visual match = {critique.matches}")
            if critique.issues and not critique.matches:
                print(f"  issues: {critique.issues}")
            if critique.matches or refine == self.max_refine:
                break
            code = self.chat.ask_code(VISUAL_REFINE_PROMPT.format(issues=critique.issues))
            self._record_generation(f"Visual-refine generation {refine + 1}", code)
            script, render = self._render_with_repair(code, out_path)
            if not render.ok:  # a refine broke the script and couldn't be repaired
                self._record("\n**Stopped: a refine broke the script.**")
                return AgentRun(
                    False, False, script, render, critique, refine + 1, self._trace_path
                )

        return AgentRun(
            True,
            bool(critique and critique.matches),
            script,
            render,
            critique,
            trace_path=self._trace_path,
        )

    def _render_with_repair(self, code: CodeResult, out_path: Path) -> tuple[Path, RenderResult]:
        """Render `code`, feeding code errors back until it runs or attempts run out."""
        render: RenderResult | None = None
        script = out_path
        for attempt in range(1, self.max_repair + 1):
            script = self._write(out_path, code)
            render = render_file(script)
            if render.ok:
                self._record(f"\n_render attempt {attempt}: OK_")
                print(f"  render attempt {attempt}: OK -> {script}")
                return script, render
            error = render.stderr.strip()[-_MAX_ERROR_CHARS:]
            self._record(f"\n_render attempt {attempt}: FAILED_\n\n```\n{error}\n```")
            print(f"  render attempt {attempt}: failed", file=sys.stderr)
            if attempt < self.max_repair:
                code = self.chat.ask_code(REFINE_PROMPT.format(error=error))
                self._record_generation("Repair generation (after render error)", code)
        return script, render

    def _critique(self, image_path: str | Path, render: RenderResult) -> CritiqueResult:
        """Show Gemini the drawing + rendered views and ask whether they match."""
        views = [render.outputs[k] for k in _VIEW_KEYS if k in render.outputs]
        if not views:  # nothing to compare against
            return CritiqueResult(matches=True, issues="")
        data = self.chat.ask_structured(
            VISUAL_CRITIQUE_PROMPT, images=[image_path, *views], schema=_CRITIQUE_SCHEMA
        )
        return CritiqueResult(matches=bool(data.get("matches")), issues=data.get("issues", ""))

    # --- tracing -----------------------------------------------------------

    def _record(self, section: str) -> None:
        """Append a markdown section to the trace and flush it to disk."""
        self._trace.append(section)
        if self._trace_path is not None:
            self._trace_path.write_text("\n".join(self._trace), encoding="utf-8")

    def _record_generation(self, label: str, code: CodeResult) -> None:
        self._record(f"\n## {label}\n\n**Reasoning:**\n\n{code.reasoning or '(none)'}")
        if code.reasoning:
            preview = " ".join(code.reasoning.split())
            ellipsis = "…" if len(preview) > _REASONING_PREVIEW_CHARS else ""
            print(f"  [{label}] {preview[:_REASONING_PREVIEW_CHARS]}{ellipsis}")

    @staticmethod
    def _write(out_path: Path, result: CodeResult) -> Path:
        out_path.write_text(result.code, encoding="utf-8")
        if result.reasoning:
            out_path.with_suffix(".reasoning.md").write_text(result.reasoning, encoding="utf-8")
        return out_path
