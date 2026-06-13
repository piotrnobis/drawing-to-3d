# AGENTS.md

Instructions for AI coding agents (Claude Code, etc.) working in this repository. Humans: read this too; it encodes our conventions.

## What this project is

drawing-to-3d reconstructs an **editable parametric CAD model (STEP)** from a technical engineering drawing, using **Gemini 3.5 Flash** plus a CadQuery verify/refine loop. See `ARCHITECTURE.md`.

## Golden rules

1. **Work incrementally. One capability per change.** Do **not** scaffold the whole project or generate large multi-module systems in a single pass. We use you as a **copilot**, not an autonomous agent. If a request is large, propose the smallest first step and stop.
2. **Don't invent scope.** Implement what's asked; leave clear `# TODO:` for what's deferred. Ask before adding frameworks, services, or dependencies.
3. **Respect the contracts.** `DrawingSpec`, the runner result, and `PipelineResult` (in `ARCHITECTURE.md`) are shared interfaces. Do not change their shape without a note in the PR/commit; downstream code depends on them.
4. **Keep dependencies minimal and pinned.** Every new package is attack surface and a security-scan finding. Justify additions.

## Tech and versions (do not drift)

- **Gemini SDK:** use the unified **`google-genai`** SDK — `from google import genai`. **Do NOT** use the deprecated `google-generativeai` package. No `genai.GenerativeModel(...)`, no `genai.configure(...)`.
- **Model string:** `gemini-3.5-flash`.
- **Auth:** `genai.Client()` reads `GEMINI_API_KEY` from the environment (an AI Studio key). Never pass a key literal.
- **Images:** `types.Part.from_bytes(data=..., mime_type=...)` inside the `contents` list.
- **CAD:** CadQuery (OpenCASCADE) for B-rep, STEP export, HLR projection, dimension queries.
- **Backend (when built):** FastAPI. **Frontend (when built):** React + Vite + TypeScript + Tailwind + react-three-fiber.
- **Python:** 3.11+, type hints, `pydantic` for data models. Format with ruff + black.
- **TS:** strict mode, eslint + prettier.

## Security rules you MUST follow

- **Never hardcode secrets.** Read them from env. Never print or log keys. Never commit `.env`.
- **Never `exec`/`eval` model-generated CadQuery in the main process.** Generated code is untrusted and must run **only** through the sandboxed runner (separate subprocess, hard timeout, clean environment without secrets, scratch temp dir, no network where feasible). If the runner does not exist yet, do not add an inline `exec` as a shortcut; flag it instead.
- **Validate uploads** (allowed image types, max size) before processing.
- In dev, keep **CORS** restricted to localhost, not `*`.

See `SECURITY.md` for the full threat model.

## How to verify your change

- After any change, run the relevant smoke test or `pytest`, and state how you verified it.
- For the Gemini helper: `python gemini.py` should return text for a plain prompt and for an image+prompt.
- Don't claim something works without running it.

## What NOT to do

- No giant one-shot scaffolds.
- No new external services or connectors beyond Gemini without asking.
- No changes to the shared contracts without calling it out.
- No `google-generativeai`, no hardcoded keys, no in-process execution of generated code.
- No unpinned or unmaintained dependencies.