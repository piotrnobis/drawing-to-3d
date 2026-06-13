"""LLM access layer. Currently a single provider: Gemini."""

from backend.llm.gemini import ask

__all__ = ["ask"]
