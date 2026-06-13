"""CAD layer: run untrusted (LLM-generated) CadQuery scripts and export them.

LLM-generated CadQuery is untrusted: it is always executed in a sandboxed
subprocess with a scrubbed environment, never `exec`'d in this process.
"""

from backend.cad.render import RenderResult, render_code, render_file

__all__ = ["RenderResult", "render_file", "render_code"]
