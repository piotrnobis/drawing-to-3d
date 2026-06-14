"""Analysis stage: Gemini reasons about the drawing before any code is written.

Produces a structured `Analysis` (description, per-view notes, and a dimension
table). The turn stays in the agent's `Conversation`, so the subsequent code
generation is grounded by this analysis; the dimension table also feeds the
dimensional gate.
"""

from pathlib import Path

from backend.agent.models import Analysis
from backend.agent.prompts import ANALYSIS_PROMPT
from backend.llm import Conversation


def analyze(chat: Conversation, image_path: str | Path) -> Analysis:
    """Run the analysis turn and return a validated `Analysis`."""
    data = chat.ask_structured(ANALYSIS_PROMPT, images=image_path, schema=Analysis)
    return Analysis.model_validate(data)
