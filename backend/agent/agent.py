"""The CAD agent: drawing -> CadQuery -> render -> visual self-critique -> refine.

`CadAgent` holds one Gemini `Conversation` (persistent system prompt + CadQuery
reference). Each run:
  1. generates a script and renders it, repairing on code errors (inner loop);
  2. shows Gemini the original drawing alongside the model's rendered views and
     asks whether they match (visual critique);
  3. if they don't, feeds the discrepancies back and regenerates (outer loop),
     bounded by `max_refine`.
Everything happens in the SAME conversation, so each step carries full context.

Each run gets its own directory `renders/run_<timestamp>/` holding every
iteration's artifacts (`iter0.*`, `iter0_repair1.*`, `iter1.*`, …), a `trace.md`
of the model's reasoning/critiques, and a `final.*` copy of the accepted model —
so iterations are preserved for analysis instead of overwriting each other.
"""

import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from google.genai import types

from backend.agent.analysis import analyze
from backend.agent.gate import GateResult, evaluate
from backend.agent.models import Analysis
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
class _Candidate:
    """One rendered attempt, kept so we can return the best (elitism)."""

    score: tuple
    script: Path
    render: RenderResult
    critique: CritiqueResult
    gate: GateResult
    refine: int


@dataclass
class AgentRun:
    ok: bool  # a model rendered successfully
    verified: bool  # passed the visual critique
    script: Path
    render: RenderResult
    critique: CritiqueResult | None = None
    refines: int = 0
    run_dir: Path | None = None
    trace_path: Path | None = None
    analysis: Analysis | None = None
    gate: GateResult | None = None

    def __bool__(self) -> bool:
        return self.ok


class CadAgent:
    def __init__(
        self,
        model: str | None = None,
        max_repair: int = 3,
        max_refine: int = 2,
        thinking: str | int | None = None,
    ):
        self.max_repair = max_repair  # code-error retries per generation
        self.max_refine = max_refine  # visual-mismatch retries
        kwargs = {"system_instruction": SYSTEM_PROMPT, "thinking": thinking}
        if model:
            kwargs["model"] = model
        self.chat = Conversation(**kwargs)
        self._run_dir: Path = Path("renders")
        self._trace: list[str] = []
        self._trace_path: Path | None = None

    def run(self, image_path: str | Path, out_dir: str | Path = "renders") -> AgentRun:
        """Generate, render, and visually refine a CadQuery model for `image_path`.

        Writes all artifacts into a fresh `<out_dir>/run_<timestamp>/` directory.
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"drawing not found: {image_path}")
        self._run_dir = self._make_run_dir(Path(out_dir))
        self._trace = []
        self._trace_path = self._run_dir / "trace.md"
        self._record(f"# Agent trace — {image_path}\n")
        print(f"run dir -> {self._run_dir}")

        analysis = self._analyze(image_path)

        code = self.chat.ask_code(USER_PROMPT, images=image_path)
        self._record_generation("Initial generation", code)

        script, render = self._render_with_repair(code, "iter0")
        if not render.ok:
            self._record("\n**Stopped: could not produce a rendering.**")
            return self._result(False, False, script, render, analysis=analysis)

        best: _Candidate | None = None
        for refine in range(self.max_refine + 1):
            critique = self._critique(image_path, render)
            gate = evaluate(analysis.dimensions, render.measurements) if analysis else GateResult()
            score = self._score(critique, gate, render)
            if best is None or score > best.score:  # elitism: keep the best candidate
                best = _Candidate(score, script, render, critique, gate, refine)

            self._record(
                f"\n## Verify {refine} — visual: {critique.matches}, "
                f"dimension gate: {'PASS' if gate.passed else 'FAIL'}\n\n"
                f"{gate.table()}\n\n"
                f"**Issues:** {critique.issues or '(none)'}\n{gate.failures()}"
            )
            print(
                f"refine {refine}: visual={critique.matches} "
                f"gate={'pass' if gate.passed else 'fail'} ({gate.n_pass} dims ok)"
            )
            if critique.issues and not critique.matches:
                print(f"  visual issues: {critique.issues}")
            if not gate.passed:
                print(f"  dimension failures:\n{gate.failures()}")

            if (critique.matches and gate.passed) or refine == self.max_refine:
                break
            feedback = self._merge_feedback(critique.issues, gate.failures())
            code = self.chat.ask_code(VISUAL_REFINE_PROMPT.format(issues=feedback))
            self._record_generation(f"Refine generation {refine + 1}", code)
            new_script, new_render = self._render_with_repair(code, f"iter{refine + 1}")
            if not new_render.ok:  # a refine broke the script; keep the best earlier one
                self._record("\n**A refine failed to render; keeping the best earlier candidate.**")
                print("  refine broke; keeping best so far", file=sys.stderr)
                break
            script, render = new_script, new_render

        verified = bool(best.critique.matches and best.gate.passed)
        self._finalize(best.script, best.render)
        self._record(f"\n## Selected best: {best.script.stem} (verified={verified})")
        print(f"selected best: {best.script.stem} (verified={verified})")
        return self._result(
            True,
            verified,
            best.script,
            best.render,
            best.critique,
            best.refine,
            analysis,
            best.gate,
        )

    def _render_with_repair(self, code: CodeResult, label: str) -> tuple[Path, RenderResult]:
        """Render `code`, feeding code errors back until it runs or attempts run out.

        Each attempt is written under a distinct name (`<label>`, `<label>_repair1`, …).
        """
        render: RenderResult | None = None
        script = self._run_dir / f"{label}.py"
        for attempt in range(1, self.max_repair + 1):
            name = label if attempt == 1 else f"{label}_repair{attempt - 1}"
            script = self._write(self._run_dir / f"{name}.py", code)
            render = render_file(script, out_dir=self._run_dir, name=name)
            if render.ok:
                self._record(f"\n_render {name}: OK_")
                print(f"  render {name}: OK")
                return script, render
            error = render.stderr.strip()[-_MAX_ERROR_CHARS:]
            self._record(f"\n_render {name}: FAILED_\n\n```\n{error}\n```")
            print(f"  render {name}: failed", file=sys.stderr)
            if attempt < self.max_repair:
                code = self.chat.ask_code(REFINE_PROMPT.format(error=error))
                self._record_generation(f"Repair generation (after {name})", code)
        return script, render

    def _critique(self, image_path: str | Path, render: RenderResult) -> CritiqueResult:
        """Verify the model: a deterministic connectivity check + Gemini's visual compare."""
        # Deterministic: a correct part is one connected solid; >1 means it fell apart.
        n_solids = render.measurements.get("solid_count", 1)
        connectivity = ""
        if n_solids > 1:
            connectivity = (
                f"The model is {n_solids} DISCONNECTED solids — it must be a single "
                "connected solid. Reposition components so mating faces overlap by a few "
                "mm, then union them all into one solid."
            )

        views = [render.outputs[k] for k in _VIEW_KEYS if k in render.outputs]
        if not views:  # nothing to compare visually; rely on the connectivity check
            return CritiqueResult(matches=not connectivity, issues=connectivity)

        data = self.chat.ask_structured(
            VISUAL_CRITIQUE_PROMPT, images=[image_path, *views], schema=_CRITIQUE_SCHEMA
        )
        issues = data.get("issues", "")
        if connectivity:  # deterministic finding overrides/leads the visual verdict
            issues = connectivity + (f"\n{issues}" if issues else "")
        return CritiqueResult(matches=bool(data.get("matches")) and not connectivity, issues=issues)

    def _analyze(self, image_path: str | Path) -> Analysis | None:
        """Reason about the drawing first; save the analysis + dimension table."""
        try:
            analysis = analyze(self.chat, image_path)
        except Exception as exc:  # noqa: BLE001 — analysis is best-effort, never fatal
            self._record(f"\n## Analysis failed\n\n{type(exc).__name__}: {exc}")
            print(f"analysis failed ({type(exc).__name__}); continuing without it", file=sys.stderr)
            return None

        (self._run_dir / "analysis.json").write_text(
            analysis.model_dump_json(indent=2), encoding="utf-8"
        )
        dims = "\n".join(
            f"- {d.label}: {d.value:g} ±{d.tolerance:g} mm ({d.kind})" for d in analysis.dimensions
        )
        self._record(
            f"\n## Analysis\n\n**Summary:** {analysis.summary}\n\n"
            f"**Guess:** {analysis.guess}\n\n**Dimensions:**\n{dims}"
        )
        print(f"analysis: {analysis.guess[:120]} | {len(analysis.dimensions)} dimensions")
        return analysis

    @staticmethod
    def _score(critique: CritiqueResult, gate: GateResult, render: RenderResult) -> tuple:
        """Rank a candidate for elitism (higher is better, compared lexicographically).

        A fully-verified model wins; then a single connected solid (a disconnected
        part is fundamentally broken); then more passing dimensions; then visual match.
        """
        connected = render.measurements.get("solid_count", 1) == 1
        return (
            int(critique.matches and gate.passed),
            int(connected),
            gate.n_pass,
            int(critique.matches),
        )

    @staticmethod
    def _merge_feedback(visual: str, dim_failures: str) -> str:
        parts = []
        if visual:
            parts.append(visual)
        if dim_failures:
            parts.append(
                "Dimension mismatches (the model's measured size is wrong):\n" + dim_failures
            )
        return "\n\n".join(parts) if parts else "(no specific issues; improve overall fidelity)"

    # --- outputs / tracing -------------------------------------------------

    @staticmethod
    def _make_run_dir(base: Path) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = base / f"run_{ts}"
        n = 1
        while run_dir.exists():
            run_dir = base / f"run_{ts}_{n}"
            n += 1
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _finalize(self, script: Path, render: RenderResult) -> None:
        """Copy the accepted iteration's artifacts to `final.*` for easy access."""
        stem = script.stem  # e.g. "iter2"
        shutil.copy2(script, self._run_dir / "final.py")
        reasoning = script.with_suffix(".reasoning.md")
        if reasoning.exists():
            shutil.copy2(reasoning, self._run_dir / "final.reasoning.md")
        for path in render.outputs.values():
            final_name = "final" + path.name[len(stem) :]  # "iter2.front.png" -> "final.front.png"
            shutil.copy2(path, self._run_dir / final_name)

    def _result(
        self, ok, verified, script, render, critique=None, refines=0, analysis=None, gate=None
    ) -> AgentRun:
        return AgentRun(
            ok,
            verified,
            script,
            render,
            critique,
            refines,
            self._run_dir,
            self._trace_path,
            analysis,
            gate,
        )

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
    def _write(script_path: Path, result: CodeResult) -> Path:
        script_path.write_text(result.code, encoding="utf-8")
        if result.reasoning:
            script_path.with_suffix(".reasoning.md").write_text(result.reasoning, encoding="utf-8")
        return script_path
