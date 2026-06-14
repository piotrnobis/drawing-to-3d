# Handoff — drawing → verified parametric CAD ("Trueform")

_Last updated: 2026-06-14, end of an overnight build session. Read this first._

## 1. The goal
Munich AI Hackathon, **Kyrall track**. Take a multi-view orthographic **engineering drawing (PNG)** and reconstruct it as an **editable parametric CAD model (STEP B-rep, not a mesh)** — then **prove it's right** two ways: a vision model checks the *shape*, and the geometry is *measured* against every dimension callout. The dimensional check is the differentiator. Single LLM provider: **Gemini** (`gemini-3.5-flash`). Product name is now **Trueform** (was "datum").

Backend is built and runs end-to-end. Colleagues started a **React frontend** (`frontend/`). The remaining big piece is an API + UI wrapping the agent.

**Hackathon constraints:** Gemini-only for the model, **minimal pinned deps**, sandboxed execution (the "most secure build" side challenge is graded via **Aikido**), AND we must use **at least one partner technology**. See §6 — current lean is **Tavily** (web retrieval), with Pioneer/Fastino fine-tuning as the analyzed-but-unlikely alternative.

## 2. Current state of the code
- **Git:** on branch `main`, commit `fc8c528`, **ahead of `origin/main` by 5 commits, NOT pushed yet** (waiting on the user). The feature branch `feat/dimensional-gate-and-manual` was merged into `main` cleanly (no conflicts — backend vs frontend were disjoint).
- **Pipeline (all in one Gemini `Conversation`):** analyze → generate → run + repair (sandboxed) → render + measure → verify (shape + size) → refine (bounded, keep-best). Works; the manifold (`samples/orthographic_3/cad-drawing.png`) was **verified on the first attempt** in the last run.
- **Packages:**
  - `backend/llm/` — Gemini access: `ask`, `ask_code` / `ask_code_json` (structured JSON → `CodeResult`), `Conversation` (stateful chat, per-turn schema, system_instruction). Has transient-retry, `max_output_tokens=32768`, `media_resolution=HIGH`, `THINKING_BUDGETS`, truncation-salvage parse.
  - `backend/cad/` — sandboxed CadQuery runner. `render_file`/`render_code` → STEP/STL/SVG/HTML viewer + 4 PNG views + measurements. `_harness.py` runs untrusted code in a subprocess (scrubbed env, timeout) and measures the B-rep.
  - `backend/agent/` — `CadAgent` (the loop), `analysis.py`, `gate.py`, `models.py` (pydantic), `prompts.py`, `cadquery_reference.md` (the manual).
- **Env:** conda env `drawing-to-3d` (Python 3.12). Deps: `cadquery` (conda; brings `vtk`+`OCP`), `google-genai==1.16.1`, `python-dotenv`, `pydantic` (pip). `pip install -e .[dev]` for ruff/black/mypy.
- **Run it:** `python -m backend.agent samples/orthographic_3/cad-drawing.png [--thinking minimal|low|medium|high|dynamic]`. Outputs go to a timestamped `renders/run_<ts>/` (gitignored) with `iter*` artifacts, `final.*`, and `trace.md` (full model reasoning + critiques — read this to debug a run).
- **Docs:** `trueform.html` (self-contained explainer for the pitch, images base64-embedded), `docs/assets/manifold-*.png` (those renders, tracked), `docs/{ARCHITECTURE,AGENTS,SECURITY}.md`. Old `datum-explainer.html` is superseded by `trueform.html`.

### Running env note (important)
The Bash tool is NOT in the conda env. Use the env's interpreter explicitly:
`/c/Users/cbarb/miniforge3/envs/drawing-to-3d/python.exe -m backend.agent ...`
Lint: `python -m ruff check backend` and `python -m black backend`. Each agent run is a few minutes and stochastic (costs API).

## 3. Files we actively edit (the iteration surface)
- `backend/agent/cadquery_reference.md` — **the CadQuery manual** (mental model, design procedure, patterns, selectors, pitfalls, worked examples). Most prompt tuning lands here.
- `backend/agent/prompts.py` — `SYSTEM_PROMPT` (embeds the manual + Z-up convention + output contract), `ANALYSIS_PROMPT`, `VISUAL_CRITIQUE_PROMPT`, `VISUAL_REFINE_PROMPT`, `REFINE_PROMPT`.
- `backend/agent/agent.py` — the loop, elitism scoring, render-with-repair, critique (+connectivity), refine.
- `backend/agent/gate.py` — dimensional gate matching.
- `backend/cad/_harness.py` — B-rep measurement (incl. `_group_holes`) + vtk render.
- `backend/llm/gemini.py` — LLM client knobs.

## 4. What worked
- **Sandboxed subprocess execution** of model-written CadQuery (never in-process). Security + isolation.
- **Structured JSON output** (reasoning+code) written straight to a file — avoids the repr/copy-paste corruption we hit early.
- **One `Conversation` across all turns** (analyze/generate/repair/critique/refine) so context carries. Per-turn config must re-include `system_instruction` (a per-message config *replaces* the session config in google-genai).
- **Z-up coordinate convention** in the prompt → fixed models generating on their side.
- **CadQuery manual + failure-derived pitfalls** → big first-try quality jump (manifold verified first-try). Key pitfalls captured: elbows via `tangentArcPoint`/`radiusArc` (NOT hand-computed `threePointArc`), named-plane normals (XY→+Z, XZ→−Y, YZ→+X), `.workplane()` takes an offset not a plane name, no `.cutDepth()`, `.fillet()` selects edges first, `hull()` needs arc-circles, drill holes after union, overlap mating parts, bores must open at faces.
- **Dimension gate** = the differentiator. Now measures **per-feature hole patterns** (count, pitch, bolt-circle PCD) by grouping cylinders → catches mis-placed/mis-spaced bolt holes deterministically (the eye can't). bbox dedup (largest dim per axis = the true overall). Verified: a wrong 30 mm pattern vs a 40 mm callout **fails** with clear feedback.
- **Two-signal verification, divided by capability:** vision judges shape/topology/openings; the gate judges exact numbers. Critique told NOT to nitpick sizes (gate's job) but TO flag missing features/openings.
- **Elitism / keep-best:** score candidates (verified > single connected solid > more gate passes > visual match), return the best — never ship a regression.
- **Connectivity check** (`solid_count > 1` ⇒ disconnected) — deterministic, no LLM.
- **Robustness:** transient-error retry w/ backoff; `max_output_tokens=32768`; salvage code from a truncated JSON reply; versioned run dirs + `trace.md`.
- **HTML viewer Z-up fix** (`THREE.Object3D.DEFAULT_UP`).

## 5. What failed / hard-won lessons
- `genai.Client()` does **not** auto-read `GEMINI_API_KEY` (it wants `GOOGLE_API_KEY`) → pass `api_key=os.environ["GEMINI_API_KEY"]` explicitly.
- Setting `max_output_tokens=8192` made truncation **worse**: it's a *thinking* model and thinking tokens share that budget → answer truncated mid-JSON. Fixed at 32768.
- `threePointArc` with a hand-computed midpoint → `GC_MakeArcOfCircle ... no result` or a misaligned/disconnected pipe. (Biggest recurring first-try failure for pipe parts.)
- Global `hole_count` (total cylinders) conflated bolt holes + bores → false fails. Disabled, then fixed via per-feature grouping.
- Sub-feature dims mistagged as `bbox_*` → compared to the overall envelope → false fails. Fixed with largest-per-axis dedup + prompt clarification.
- An over-nitpicky visual critique churned already-good models and caused regressions (e.g. fixing a boss broke a rib). Fixed with keep-best + anti-regression refine prompt + the labour-division reframe.
- **Missing/blind bores still slip past sometimes:** the gate checks a diameter *exists* (not its location/through-ness), and the eye can miss a small opening. Mitigated (manual open-bore rule + critique openings check) but a *deterministic* through-ness/location check is still TODO.
- `google-genai 1.16.1` has **no named `thinking_level`** — only `thinking_budget` (int). We map levels→budgets in `THINKING_BUDGETS`.
- **Fine-tuning (Fastino/Pioneer + Gemma) analysis:** don't replace Flash — the bottleneck is multimodal spatial reasoning (Flash ≫ Gemma) and Pioneer fine-tunes *text* models only. The only sound use is a **text→CadQuery** code model placed *after* the analysis stage (a stretch; needs the structured spec). Full memo in the plan file.

## 6. Partner technology (hackathon requirement) — Tavily (leading) vs Pioneer
We must use ≥1 partner technology beyond the base stack. Two candidates:
- **Tavily (web retrieval) — the likely pick.** Natural fit, low risk, independently useful. Concrete uses:
  1. **Standard-part data:** fetch standard dimensions (flange tables, bolt/thread sizes, pipe schedules, ISO/DIN norms) to fill gaps in the drawing's dimension table or sanity-check callouts — this also improves the gate's ground truth.
  2. **CadQuery docs/examples as RAG:** retrieve relevant API usage/examples at generation time to ground the code (complements or refreshes the static `cadquery_reference.md` manual).
  3. **Part identification:** web-ground the analysis "what is this part" guess (e.g. recognise a standard fitting) to inform reconstruction.
  - **Where it slots in:** mainly the **analysis** stage (enrich/validate the spec) and **generation grounding**. Keep it a thin, cached layer (≈one Tavily call per run, results fed into the prompt) to control latency/cost.
- **Pioneer / Fastino (fine-tuning) — analyzed, unlikely.** The bottleneck is multimodal spatial reasoning (Flash ≫ Gemma) and Pioneer fine-tunes *text-only* models; the only sound use is a text→CadQuery code model *after* the analysis stage (a stretch). Full memo in the plan file.
- **Decision:** if we don't fine-tune with Pioneer (current lean), **use Tavily** to satisfy the requirement. (Aikido covers the separate "most secure build" challenge.)

## 7. Plan & next steps (recommended order)
1. **Push `main` to `origin`** (was pending the user's OK at end of session): `git push origin main`. Optionally delete `feat/dimensional-gate-and-manual`.
2. **FastAPI endpoint around `CadAgent`** + wire to the existing `frontend/` (React screens already exist: Upload/Read/Build/Verify/Preview/Export). This is the biggest remaining piece for the demo — turn the working backend into the live UI.
3. **Integrate Tavily (partner tech, §6):** a thin, cached retrieval step in the **analysis** stage — standard-part dimensions + CadQuery examples fed into the prompt. Satisfies the partner-tech requirement and improves the dimension table / generation grounding.
4. **Close measurement gaps** (extends the differentiator): deterministic **through-ness / location** of bores (catch missing open bores), then `thickness`, then between-feature `spacing`. Each turns currently-`unmeasured` dims into real pass/fail.
5. **Project-back overlay** as a second shape signal (HLR line views vs the drawing). Colleague's `projection.py` (repo root) already does HLR but uses `OCC.Core` + `matplotlib` (NOT installed here) — **port it to `OCP`** (cadquery's binding) + a rasterizer rather than adding pythonocc.
6. Optional polish: A/B the `--thinking` levels; tune `THINKING_BUDGETS`; more hero part classes.
7. Stretch: text→CadQuery fine-tune via Fastino — only if we go that route instead of Tavily (§6), after the analysis spec stabilizes (see plan memo).
8. **Hackathon deliverables** still open: 2-min demo video, Aikido security report screenshot, working pipeline on 2–3 hero parts with a passing dimension table.

## 8. Pointers
- Full evolving plan + fine-tuning memo: `~/.claude/plans/luminous-dancing-coral.md`.
- `samples/orthographic_3/cad-drawing.png` is the main test part (a multi-flange manifold). New untracked-then-committed samples: `cad3..cad6.png`.
- To inspect a run: open `renders/run_<ts>/final.html` (3D viewer) and read `renders/run_<ts>/trace.md`.
- This `handoff.md` is currently untracked — commit it with the next push if you want it in history.
