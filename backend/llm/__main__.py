"""Smoke test: `python -m backend.llm` sends a text prompt and prints the reply."""

from backend.llm.gemini import ask

if __name__ == "__main__":
    print(ask("Say hello in one short sentence."))
