"""Loads all prompt text from config/prompts/ at call time.

Edit the .md files in that directory to change model behaviour — no Python
changes required. Placeholder syntax: <<<PLACEHOLDER_NAME>>> (uppercase, triple
angle brackets). This avoids conflicts with JSON curly braces in the prompt files.
"""

import json
from pathlib import Path

# Project root → config/prompts/
_PROMPTS_DIR = Path(__file__).parents[2] / "config" / "prompts"


def _read(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}\n"
            f"Expected all prompt files inside: {_PROMPTS_DIR}"
        )
    return path.read_text(encoding="utf-8")


def _inject(template: str, **substitutions: str) -> str:
    """Replace <<<KEY>>> markers in template with the given values."""
    result = template
    for key, value in substitutions.items():
        result = result.replace(f"<<<{key.upper()}>>>", value)
    return result


def get_system_prompt() -> str:
    """Build the system prompt by injecting the CadQuery reference into system.md."""
    template = _read("system.md")
    reference = _read("cadquery_reference.md")
    return _inject(template, cadquery_reference=reference)


def format_user_prompt(params: dict | None = None) -> str:
    """Build the 5-step user prompt, optionally injecting an authoritative dimension table."""
    template = _read("user.md")
    if params:
        params_block = "```json\n" + json.dumps(params, indent=2) + "\n```"
    else:
        params_block = (
            "No dimension table provided — read all values directly from "
            "the drawing annotations."
        )
    return _inject(template, params_block=params_block)


def format_refine_prompt(error: str) -> str:
    """Build the refinement prompt with the render error injected."""
    return _inject(_read("refine.md"), error=error)
