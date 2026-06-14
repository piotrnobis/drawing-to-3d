# Architecture

How Ortograph turns a 2D engineering drawing into a verified, editable CAD model.

## Goal and the hard constraint

Take a multi-view orthographic engineering drawing and reconstruct it as an **editable parametric
CAD model** (STEP — a real B-rep), then **prove it is correct**.

The output must be parametric, **not a mesh**. A generated triangle soup looks fine and is useless:
you cannot edit a wall thickness or re-fit a bore on it. And a part that *looks* right but
*measures* wrong is worthless for a replacement part — so verification is the core of the project,
not an add-on.

## The pipeline

Everything runs inside **one Gemini `Conversation`** (`backend/agent/agent.py` → `CadAgent.run`), so
each step carries the full context of the ones before it.

1. **Analyze** (`analysis.py`) — drawing → a structured `Analysis`: summary, per-view notes, and a
   **dimension table** (every callout with value, tolerance, and a typed `kind`). The table is the
   ground truth the dimension gate checks against.
2. **Generate** (`prompts.py`, `retrieval.py`) — Gemini writes **CadQuery** code, grounded by an
   embedded CadQuery manual (`cadquery_reference.md`) and a few examples fetched live via **Tavily**.
   For complex parts it builds **one feature at a time** (staged build, below).
3. **Run + repair** (`backend/cad/`) — the untrusted script runs in a **sandboxed subprocess**; on a
   code error the traceback is fed back and the model fixes it, before any verification.
4. **Render + measure** (`_harness.py`) — export STEP/STL/SVG, render 4 views (front/top/side/iso,
   clay-gray with feature edges so cuts read clearly), and **measure the B-rep**: bounding box,
   per-feature **hole patterns** (count, pitch, bolt-circle PCD), and a **solid count** (connectivity).
5. **Verify** — the three signals below.
6. **Refine** — if a check fails, the discrepancies are fed back and the model edits the **best
   working script so far** (a minimal change, not a rewrite, to avoid regressions). Bounded
   iterations with **elitism**: always return the best candidate seen.

Each run writes a versioned `renders/run_<ts>/` with per-iteration artifacts, `final.*`, and a full
`trace.md` of the model's reasoning and critiques.

## Verification = three signals

This is the differentiator. The eye, an independent second opinion, and the ruler catch different
errors, and the labour is divided cleanly.

- **Eye — shape** (`_critique`, `VISUAL_CRITIQUE_PROMPT`): in-conversation, Gemini compares the 4
  rendered views to the drawing and flags only **obvious, structural** differences (missing/extra
  feature, a bore that should be open but is solid, a feature on the wrong face, disconnected
  parts). Small details and exact sizes are deliberately ignored — that's the gate's job — so a good
  model isn't nitpicked into a worse one. A deterministic **connectivity check** backs it up: more
  than one solid means the part fell apart.
- **Judge — independent second opinion** (`_confirm_with_judge`, `JUDGE_PROMPT`): the self-critique
  shares the generator's context and tends to rationalize its own intent. So before trusting a pass,
  a **separate, stronger model** (`gemini-3.1-pro-preview`) is called **statelessly — no system
  prompt, no history** — and shown only the drawing + renders. It runs *only* when the cheap critique
  already claims a pass, applies a high bar, and vetoes false positives.
- **Ruler — size** (`gate.py`): query the actual B-rep and check each callout within tolerance.
  Beyond bbox and bore diameters, it verifies **hole patterns precisely** (count, hole-to-hole
  pitch, bolt-circle diameter) per flange — catching mis-placed screws the eye cannot judge. Every
  verdict reports its **coverage** (e.g. `PASS · 15/30 verified, 15 unmeasured`) so a thin check
  never masquerades as a strong one; kinds we can't measure yet stay `unmeasured`, never a false pass.

A model is **verified** only when eye **and** judge **and** gate agree.

## Staged build (complex parts)

A single 200-line script for a complex part is brittle — fix one feature and the model rewrites the
whole thing, breaking three others. So `_staged_build` (auto-enabled when the analysis has many
dimension callouts; force with `--staged` / `--no-staged`):

1. **Plans** the part as an ordered feature list (`PLAN_PROMPT` → `BuildPlan`): all positive solids
   first, then all cuts.
2. Builds them **one at a time** — each stage is handed the *last script that rendered* and adds
   exactly one feature.
3. **Locks** each stage after it renders and passes a connectivity + gate check, so a feature can
   only ever stack on a solid that already works.

The result is a structurally sound base that the normal refine loop then polishes. (Per-stage
verification is deterministic — connectivity + gate; the visual eye/judge run once at the end.)

## Sandbox & security

Generated CadQuery is **arbitrary code execution**, so it runs **only** through the sandboxed runner
(`render.py` → `_harness.py`): a separate subprocess, a scrubbed environment (no secrets inherited),
a hard timeout, and gitignored scratch output. It is never `exec`'d in the app process. Full threat
model in [`SECURITY.md`](SECURITY.md).

## Frontend (demo app)

`frontend/` is a React (TanStack Start + Vite) app that **replays real runs** from bundled artifacts
(`frontend/public/demo/`): pick a sample, watch the staged reconstruction, inspect the 3D STEP model
(occt-import-js + three.js), see the live dimension-gate table, and download STEP/STL. It is not
wired to the live backend yet — a `DrawingRunner` interface (`src/demo/runner.ts`) isolates the data
source, so an `ApiRunner` posting to a future FastAPI endpoint drops in with no UI changes.

## Partner technology — Tavily

`retrieval.py` fetches a few CadQuery code examples at generation time to ground the model
(best-effort and optional — it no-ops cleanly without a `TAVILY_API_KEY`).

## Roadmap / not yet built

- **More measured dimension kinds** — `thickness`, feature `spacing`, bore through-ness/location.
  This is the highest-value next step (it widens the gate's coverage, the differentiator).
- **Live backend** — a FastAPI endpoint around `CadAgent`, wired behind the frontend's `DrawingRunner`.
- **Project-back overlay** — re-draw the solid as orthographic line views and overlay on the input
  (HLR via OCP) as a second, localizing shape signal.
- **Prompt-to-edit** — natural-language edits to the finished model before export (the demo UI
  already teases this).

## Prior art (for grounding)

VLM + CadQuery + visual-refinement loops (CADCodeVerify, 3D-Premise, Seek-CAD) are our lineage;
CAD2Program shows the pure-VLM route needs heavy domain data, which is why we lean on **validation**
instead. DeepCAD / Text2CAD define the sketch→extrude vocabulary we constrain generation to.
