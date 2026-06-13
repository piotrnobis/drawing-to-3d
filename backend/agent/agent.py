"""The CAD agent: drawing -> CadQuery -> render, self-refining within one chat.

`CadAgent` holds a single Gemini `Conversation` (persistent system prompt +
CadQuery reference). It generates a script, renders it in the sandbox, and on
failure feeds the error back into the SAME conversation so the model fixes its
own prior code with full context — repeating up to `max_attempts`.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

from backend.agent.prompts import REFINE_PROMPT, SYSTEM_PROMPT, USER_PROMPT
from backend.cad import RenderResult, render_file
from backend.llm import CodeResult, Conversation

# Tracebacks can be long; the actionable part is the tail. Keep tokens sane.
_MAX_ERROR_CHARS = 2000


@dataclass
class AgentRun:
    ok: bool
    script: Path
    render: RenderResult
    attempts: int

    def __bool__(self) -> bool:
        return self.ok


class CadAgent:
    def __init__(self, model: str | None = None, max_attempts: int = 3):
        self.max_attempts = max_attempts
        kwargs = {"system_instruction": SYSTEM_PROMPT, "code_json": True}
        if model:
            kwargs["model"] = model
        self.chat = Conversation(**kwargs)

    def run(self, image_path: str | Path, out_path: str | Path = "generated.py") -> AgentRun:
        """Generate and render a CadQuery model for `image_path`, refining on errors."""
        out_path = Path(out_path)
        result = self.chat.ask_code(USER_PROMPT, images=image_path)

        render: RenderResult | None = None
        for attempt in range(1, self.max_attempts + 1):
            script = self._write(out_path, result)
            render = render_file(script)
            if render.ok:
                print(f"attempt {attempt}: OK -> {script}")
                return AgentRun(True, script, render, attempt)

            print(f"attempt {attempt}: render failed", file=sys.stderr)
            if attempt < self.max_attempts:
                error = render.stderr.strip()[-_MAX_ERROR_CHARS:]
                result = self.chat.ask_code(REFINE_PROMPT.format(error=error))

        return AgentRun(False, script, render, self.max_attempts)

    @staticmethod
    def _write(out_path: Path, result: CodeResult) -> Path:
        out_path.write_text(result.code, encoding="utf-8")
        if result.reasoning:
            out_path.with_suffix(".reasoning.md").write_text(result.reasoning, encoding="utf-8")
        return out_path
