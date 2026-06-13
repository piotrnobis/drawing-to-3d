"""Minimal Gemini access via the unified google-genai SDK.

Send a text prompt plus optional image(s) and get text back, plus a helper that
returns runnable code — via structured JSON output (reasoning + code) so the
code field is never wrapped in markdown and can't be truncated mid-fence.
"""

import json
import mimetypes
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # loads GEMINI_API_KEY from .env

DEFAULT_MODEL = "gemini-3.5-flash"


@dataclass
class CodeResult:
    """A reasoned code reply: the model's analysis plus the runnable script."""

    reasoning: str
    code: str


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Lazily build (and cache) the client so importing this module is side-effect-free."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _image_part(image_path: str | Path) -> types.Part:
    path = Path(image_path)
    mime, _ = mimetypes.guess_type(path)
    return types.Part.from_bytes(data=path.read_bytes(), mime_type=mime or "image/png")


def _build_contents(prompt: str, images) -> list:
    if isinstance(images, (str, Path)):
        images = [images]
    contents: list = [prompt]
    for image_path in images or []:
        contents.append(_image_part(image_path))
    return contents


def ask(
    prompt: str,
    images: str | Path | Sequence[str | Path] | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Send `prompt` (and any `images`) to Gemini and return the reply text.

    `images` accepts a single path or a list of paths; mime type is inferred
    from each file extension.
    """
    contents = _build_contents(prompt, images)
    return _get_client().models.generate_content(model=model, contents=contents).text


# Structured output: the model reasons first, then emits code, as two JSON
# fields. `property_ordering` keeps reasoning before code so the chain-of-thought
# still happens prior to generating the script.
_CODE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "reasoning": types.Schema(
            type=types.Type.STRING,
            description="Step-by-step analysis of the views, coordinate system, dimensions and features.",
        ),
        "code": types.Schema(
            type=types.Type.STRING,
            description="Complete runnable Python script. Raw source only — no markdown fences.",
        ),
    },
    required=["reasoning", "code"],
    property_ordering=["reasoning", "code"],
)

_FENCED_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code(text: str) -> str:
    """Pull the runnable code out of a free-text reply (fallback path).

    Returns the last fenced code block (the model's final answer after any
    reasoning). If the reply has no fences, returns it stripped as-is.
    """
    blocks = _FENCED_BLOCK.findall(text)
    code = blocks[-1] if blocks else text
    return code.strip() + "\n"


_CODE_CONFIG = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=_CODE_SCHEMA,
)


def _parse_code(text: str) -> CodeResult:
    """Turn a model reply into a `CodeResult`.

    Prefers the structured JSON; falls back to scraping a fenced block so a
    malformed response still yields usable code (no extra API call).
    """
    try:
        data = json.loads(text)
        code = (data.get("code") or "").strip()
        if code:
            return CodeResult(reasoning=data.get("reasoning", ""), code=code + "\n")
    except (json.JSONDecodeError, TypeError):
        pass
    return CodeResult(reasoning="", code=extract_code(text))


def ask_code_json(
    prompt: str,
    images: str | Path | Sequence[str | Path] | None = None,
    model: str = DEFAULT_MODEL,
) -> CodeResult:
    """Ask for code via structured JSON; return a `CodeResult` (stateless)."""
    resp = _get_client().models.generate_content(
        model=model,
        contents=_build_contents(prompt, images),
        config=_CODE_CONFIG,
    )
    return _parse_code(resp.text)


def ask_code(
    prompt: str,
    images: str | Path | Sequence[str | Path] | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Like `ask`, but returns only the runnable code (model still reasons first)."""
    return ask_code_json(prompt, images=images, model=model).code


class Conversation:
    """A stateful Gemini chat: keeps full history across turns.

    Use this for the refine loop so a "fix this error" follow-up carries the
    model's own prior reasoning and code as context, instead of starting cold.

        chat = Conversation()
        first = chat.ask_code("Recreate this drawing...", images="part.png")
        # render fails ->
        fixed = chat.ask_code(f"That failed:\\n{error}\\nReturn the full fixed script.")
    """

    def __init__(self, model: str = DEFAULT_MODEL, *, system_instruction: str | None = None):
        """Open a chat session with a persistent `system_instruction`.

        The system instruction is applied per turn (see `_config`) rather than
        baked into the session, so different turns can request different response
        schemas (code vs. a critique vs. analysis) without dropping the persona.
        """
        self._system_instruction = system_instruction
        self._chat = _get_client().chats.create(model=model)

    def _config(self, schema=None) -> types.GenerateContentConfig:
        """Build a per-turn config. A per-message config replaces the session
        config entirely, so the system instruction must be re-included here."""
        config = types.GenerateContentConfig()
        if self._system_instruction:
            config.system_instruction = self._system_instruction
        if schema is not None:
            config.response_mime_type = "application/json"
            config.response_schema = schema
        return config

    def ask(
        self,
        prompt: str,
        images: str | Path | Sequence[str | Path] | None = None,
    ) -> str:
        """Send a turn, return reply text. History is retained automatically."""
        return self._chat.send_message(_build_contents(prompt, images), config=self._config()).text

    def ask_code(
        self,
        prompt: str,
        images: str | Path | Sequence[str | Path] | None = None,
    ) -> CodeResult:
        """Send a turn asking for code (structured JSON); return a `CodeResult`."""
        resp = self._chat.send_message(
            _build_contents(prompt, images), config=self._config(_CODE_SCHEMA)
        )
        return _parse_code(resp.text)

    def ask_structured(
        self,
        prompt: str,
        images: str | Path | Sequence[str | Path] | None = None,
        *,
        schema,
    ) -> dict:
        """Send a turn constrained to `schema`; return the parsed JSON dict."""
        resp = self._chat.send_message(_build_contents(prompt, images), config=self._config(schema))
        return json.loads(resp.text)
