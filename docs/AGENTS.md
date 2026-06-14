# AGENTS.md

Instructions for AI coding agents (Claude Code, etc.) working in this repository. Humans: read this too; it encodes our conventions.

## What this project is

Ortograph reconstructs an **editable parametric CAD model (STEP)** from a technical engineering drawing, using **Gemini** (a fast vision model for the loop, a Pro tier as an independent judge) plus a CadQuery verify/refine loop. See `ARCHITECTURE.md`.

## Golden rules

1. **Work incrementally. One capability per change.** Do **not** scaffold the whole project or generate large multi-module systems in a single pass. We use you as a **copilot**, not an autonomous agent. If a request is large, propose the smallest first step and stop.
2. **Don't invent scope.** Implement what's asked; leave clear `# TODO:` for what's deferred. Ask before adding frameworks, services, or dependencies.
3. **Respect the shared types.** The pydantic models in `agent/models.py` (`Analysis`, `Dimension`, `BuildPlan`) and the runner's `RenderResult` (`cad/render.py`) are interfaces multiple modules depend on. Don't change their shape without a note in the PR/commit.
4. **Keep dependencies minimal and pinned.** Every new package is attack surface and a security-scan finding. Justify additions.

## Tech and versions (do not drift)

- **Gemini SDK:** use the unified **`google-genai`** SDK — `from google import genai`. **Do NOT** use the deprecated `google-generativeai` package. No `genai.GenerativeModel(...)`, no `genai.configure(...)`.
- **Model strings:** the loop uses `gemini-3.5-flash`; the independent judge uses `gemini-3.1-pro-preview` (`JUDGE_MODEL` in `gemini.py`, env-overridable).
- **Auth:** `genai.Client(api_key=os.environ["GEMINI_API_KEY"])` — read the AI Studio key from the env and pass it explicitly. The SDK does **not** auto-read `GEMINI_API_KEY` (only `GOOGLE_API_KEY`), so the explicit `api_key=` is required. Never hardcode a key literal. `.env` is loaded via `python-dotenv`.
- **Images:** `types.Part.from_bytes(data=..., mime_type=...)` inside the `contents` list.
- **CAD:** CadQuery (OpenCASCADE) for B-rep, STEP export, HLR projection, dimension queries.
- **Frontend:** React + TanStack Start + Vite + TypeScript + Tailwind (in `frontend/`, demo-only — replays bundled runs). **Backend API (when built):** FastAPI, behind the frontend's `DrawingRunner` seam.
- **Python:** 3.12 (via conda — CadQuery needs it), type hints, `pydantic` for the shared data models (`Analysis`, `Dimension`, `BuildPlan`). Format with ruff + black; config in `pyproject.toml`.
- **TS:** strict mode, eslint + prettier.

## Module map and how to run

- `backend/llm/` — Gemini access: `ask`, `ask_code` / `ask_code_json` (structured JSON → `CodeResult`), `Conversation` (stateful chat with `system_instruction`, structured per-turn schemas, transient-retry, `max_output_tokens`, `media_resolution`, thinking-budget). Smoke test: `python -m backend.llm`.
- `backend/cad/` — sandboxed CadQuery runner. `render_file` / `render_code` run an **untrusted** script in a subprocess and export STEP/STL/SVG + HTML viewer + 4 PNG views, and **measure the B-rep** (bbox, per-feature hole patterns, solid count) → `RenderResult`. `_harness.py` is the only place code is exec'd (in the child). CLI: `python -m backend.cad samples/cad/bracket.py`.
- `backend/agent/` — the loop: `agent.py` (`CadAgent`: analyze → generate (one-shot or **staged** feature-by-feature) → run+repair → render+measure → **verify (eye critique + independent judge + dimension gate)** → refine, with elitism/keep-best); `analysis.py` (drawing → `Analysis`); `gate.py` (dimension gate); `models.py` (pydantic `Analysis`/`Dimension`/`BuildPlan`); `retrieval.py` (optional Tavily examples); `prompts.py` + `cadquery_reference.md` (**the CadQuery manual** — tune prompts here). CLI: `python -m backend.agent <drawing.png> [--staged|--no-staged] [--thinking minimal|low|medium|high|dynamic]`.

Setup: `conda env create -f environment.yml && conda activate drawing-to-3d && pip install -e .[dev]`. Each agent run writes a versioned `renders/run_<ts>/` (gitignored) with per-iteration artifacts + `trace.md` (read this to debug).

## Conventions when extending
- **Tune model behaviour in `cadquery_reference.md` (the manual) and `prompts.py`**, not by hardcoding part logic. New recurring failures → add a pitfall to the manual.
- **New dimension checks:** add a `kind` to `models.py` (`DimensionKind`), measure it in `_harness.py`, match it in `gate.py`. Keep the gate honest — unmeasurable kinds stay `unmeasured`, never a false pass.
- **Verification is split by capability and runs three ways:** the in-context vision critique and a **stateless independent judge** judge *shape* (presence/topology/openings); the gate judges *exact numbers*. Don't make the visual checks police sizes, and keep the judge stateless (no system prompt / history) so it stays independent.
- **Partner tech:** **Tavily** (web retrieval) is wired in `retrieval.py` — fetches CadQuery examples to ground generation; best-effort and optional (no-ops without a key).

## Security rules you MUST follow

- **Never hardcode secrets.** Read them from env. Never print or log keys. Never commit `.env`.
- **Never `exec`/`eval` model-generated CadQuery in the main process.** Generated code is untrusted and must run **only** through the sandboxed runner (separate subprocess, hard timeout, clean environment without secrets, scratch temp dir, no network where feasible). If the runner does not exist yet, do not add an inline `exec` as a shortcut; flag it instead.
- **Validate uploads** (allowed image types, max size) before processing.
- In dev, keep **CORS** restricted to localhost, not `*`.

See `SECURITY.md` for the full threat model.

## How to verify your change

- After any change, run the relevant smoke test or `pytest`, and state how you verified it.
- For the Gemini helper: `python -m backend.llm` should return text for a plain prompt.
- For the CAD runner: `python -m backend.cad samples/cad/bracket.py` should write `renders/bracket.{step,stl,svg,html}`.
- For the agent: `python -m backend.agent samples/orthographic_3/cad-drawing.png`.
- Don't claim something works without running it.

## What NOT to do

- No giant one-shot scaffolds.
- No new external services or connectors beyond Gemini without asking.
- No changes to the shared contracts without calling it out.
- No `google-generativeai`, no hardcoded keys, no in-process execution of generated code.
- No unpinned or unmaintained dependencies.