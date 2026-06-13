"""Minimal Gemini access via the unified google-genai SDK.

Send a text prompt plus optional image(s) and get text back, plus a helper that
returns runnable code — via structured JSON output (reasoning + code) so the
code field is never wrapped in markdown and can't be truncated mid-fence.
"""

import json
import mimetypes
import os
import re
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

load_dotenv()  # loads GEMINI_API_KEY from .env

DEFAULT_MODEL = "gemini-3.5-flash"

# gemini-3.5-flash is a "thinking" model: internal thinking tokens count against
# max_output_tokens, so this budget must cover BOTH the thinking and the visible
# JSON answer (reasoning + a ~200-line script). Too low truncates the answer
# mid-string. Keep it generous.
_MAX_OUTPUT_TOKENS = 32768

# Engineering drawings carry fine dimension text — send images at high resolution
# so the model gets more tokens/detail per image.
_MEDIA_RESOLUTION = types.MediaResolution.MEDIA_RESOLUTION_HIGH

# This SDK has no named "thinking level"; emulate AI Studio's Minimal/Low/Medium/
# High by mapping to a `thinking_budget` (tokens, shared with max_output_tokens).
# -1 = dynamic (model decides). Values are approximate and tunable.
THINKING_BUDGETS = {
    "minimal": 512,
    "low": 2048,
    "medium": 8192,
    "high": 24576,
    "dynamic": -1,
}


def _resolve_thinking_budget(thinking: str | int | None) -> int | None:
    """Map a named level or pass through an int; None means leave the model default."""
    if thinking is None or isinstance(thinking, int):
        return thinking
    if thinking not in THINKING_BUDGETS:
        raise ValueError(f"unknown thinking level {thinking!r}; use {list(THINKING_BUDGETS)}")
    return THINKING_BUDGETS[thinking]


# Long multi-call runs hit the occasional transient network/server error; retry
# those with backoff instead of letting one hiccup kill the whole pipeline.
_RETRY_ATTEMPTS = 3
_RETRY_BASE_DELAY = 2.0  # seconds, doubled each attempt


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


def _is_transient(exc: Exception) -> bool:
    """Whether a Gemini call failure is worth retrying (network / 5xx / rate limit)."""
    if isinstance(exc, httpx.TransportError):  # connect/read/timeout/protocol errors
        return True
    if isinstance(exc, genai_errors.ServerError):  # 5xx
        return True
    return getattr(exc, "code", None) in (429, 500, 502, 503, 504)


def _retry(call):
    """Run `call()`, retrying transient failures with exponential backoff."""
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001 — re-raised unless transient
            if attempt == _RETRY_ATTEMPTS - 1 or not _is_transient(exc):
                raise
            delay = _RETRY_BASE_DELAY * (2**attempt)
            print(
                f"  transient API error ({type(exc).__name__}); retrying in {delay:.0f}s",
                file=sys.stderr,
            )
            time.sleep(delay)


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
    resp = _retry(lambda: _get_client().models.generate_content(model=model, contents=contents))
    return resp.text


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
    max_output_tokens=_MAX_OUTPUT_TOKENS,
    media_resolution=_MEDIA_RESOLUTION,
)


_TRUNCATED_CODE = re.compile(r'"code"\s*:\s*"(.*)', re.DOTALL)


def _parse_code(text: str) -> CodeResult:
    """Turn a model reply into a `CodeResult`.

    Prefers the structured JSON. If that won't parse (e.g. a truncated response),
    falls back to a fenced block, then to salvaging the partial `code` field — so
    we never write a raw JSON blob to a `.py` file.
    """
    try:
        data = json.loads(text)
        code = (data.get("code") or "").strip()
        if code:
            return CodeResult(reasoning=data.get("reasoning", ""), code=code + "\n")
    except (json.JSONDecodeError, TypeError):
        pass

    if "```" in text:  # free-text reply with a fenced block
        return CodeResult(reasoning="", code=extract_code(text))

    # Truncated/!= JSON: salvage the partial `code` string value (un-escape it)
    # rather than dumping the JSON object as Python.
    match = _TRUNCATED_CODE.search(text)
    if match:
        raw = match.group(1)
        raw = raw[: raw.rfind('"')] if raw.rstrip().endswith('"') else raw
        try:
            code = raw.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            code = raw
        return CodeResult(reasoning="", code=code.strip() + "\n")

    return CodeResult(reasoning="", code=extract_code(text))


def ask_code_json(
    prompt: str,
    images: str | Path | Sequence[str | Path] | None = None,
    model: str = DEFAULT_MODEL,
) -> CodeResult:
    """Ask for code via structured JSON; return a `CodeResult` (stateless)."""
    resp = _retry(
        lambda: _get_client().models.generate_content(
            model=model,
            contents=_build_contents(prompt, images),
            config=_CODE_CONFIG,
        )
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

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        system_instruction: str | None = None,
        thinking: str | int | None = None,
        media_resolution=_MEDIA_RESOLUTION,
    ):
        """Open a chat session with a persistent `system_instruction`.

        The system instruction (plus media resolution and thinking budget) is
        applied per turn (see `_config`) rather than baked into the session, so
        different turns can request different response schemas (code vs. a
        critique vs. analysis) without dropping the persona.

        `thinking` is a named level ("minimal"/"low"/"medium"/"high"/"dynamic")
        or a raw `thinking_budget` int; None leaves the model default.
        """
        self._system_instruction = system_instruction
        self._thinking_budget = _resolve_thinking_budget(thinking)
        self._media_resolution = media_resolution
        self._chat = _get_client().chats.create(model=model)

    def _config(self, schema=None) -> types.GenerateContentConfig:
        """Build a per-turn config. A per-message config replaces the session
        config entirely, so the system instruction must be re-included here."""
        config = types.GenerateContentConfig(max_output_tokens=_MAX_OUTPUT_TOKENS)
        if self._media_resolution is not None:
            config.media_resolution = self._media_resolution
        if self._system_instruction:
            config.system_instruction = self._system_instruction
        if self._thinking_budget is not None:
            config.thinking_config = types.ThinkingConfig(thinking_budget=self._thinking_budget)
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
        resp = _retry(
            lambda: self._chat.send_message(_build_contents(prompt, images), config=self._config())
        )
        return resp.text

    def ask_code(
        self,
        prompt: str,
        images: str | Path | Sequence[str | Path] | None = None,
    ) -> CodeResult:
        """Send a turn asking for code (structured JSON); return a `CodeResult`."""
        resp = _retry(
            lambda: self._chat.send_message(
                _build_contents(prompt, images), config=self._config(_CODE_SCHEMA)
            )
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
        resp = _retry(
            lambda: self._chat.send_message(
                _build_contents(prompt, images), config=self._config(schema)
            )
        )
        return json.loads(resp.text)
