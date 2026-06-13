"""Minimal Gemini access via the unified google-genai SDK.

Single capability: send a text prompt plus optional image(s) and get text back.
"""

import mimetypes
import os
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # loads GEMINI_API_KEY from .env

DEFAULT_MODEL = "gemini-3.5-flash"

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


def ask(
    prompt: str,
    images: str | Path | Sequence[str | Path] | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Send `prompt` (and any `images`) to Gemini and return the reply text.

    `images` accepts a single path or a list of paths; mime type is inferred
    from each file extension.
    """
    if isinstance(images, (str, Path)):
        images = [images]

    contents: list = [prompt]
    for image_path in images or []:
        contents.append(_image_part(image_path))

    return _get_client().models.generate_content(model=model, contents=contents).text


if __name__ == "__main__":
    print(ask("Say hello in one short sentence."))
