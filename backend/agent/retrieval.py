"""Optional CadQuery-example retrieval via Tavily (partner technology).

A thin, best-effort, single-call layer: given the part's likely identity/features,
fetch a few CadQuery code examples to ground the initial generation. It is designed
to interfere with nothing — it degrades to a no-op (returns "") whenever the
``TAVILY_API_KEY`` is absent, the ``tavily`` package is not installed, or anything
goes wrong. The agent only augments its prompt when this returns a non-empty string.
"""

import os
import sys

_MAX_RESULTS = 3  # keep it small — a few grounding snippets, not a dump
_MAX_CHARS = 1600  # cap the injected context so it never dominates the prompt


def fetch_cadquery_examples(query: str) -> str:
    """Return a short markdown block of CadQuery examples for `query`, or "" on any failure.

    Never raises: a missing key/package or a network/API error just yields "" so the
    pipeline runs exactly as it would without retrieval.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or not query.strip():
        return ""
    try:
        from tavily import TavilyClient  # lazy: optional dep, absent install => no-op

        client = TavilyClient(api_key=api_key)
        resp = client.search(
            f"CadQuery python example: {query}",
            max_results=_MAX_RESULTS,
        )
    except Exception as exc:  # noqa: BLE001 — retrieval is best-effort, never fatal
        print(f"  Tavily retrieval skipped ({type(exc).__name__})", file=sys.stderr)
        return ""

    results = resp.get("results", []) if isinstance(resp, dict) else []
    blocks = []
    for r in results:
        content = (r.get("content") or "").strip()
        if content:
            title = r.get("title") or "example"
            url = r.get("url") or ""
            blocks.append(f"- {title} ({url}):\n{content}")
    return "\n\n".join(blocks)[:_MAX_CHARS]
