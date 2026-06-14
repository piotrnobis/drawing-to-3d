# Ortograph

**Turn a 2D engineering drawing into a verified, editable 3D CAD model.**

Ortograph reads a multi-view orthographic engineering drawing and reconstructs it as a real
**parametric STEP model** (a B-rep you can edit — *not* a mesh) — then **proves it is right three
ways**: a vision critique looks at it, an independent judge double-checks, and the geometry is
measured against every dimension callout.

Built for the Munich AI Hackathon (Kyrall track). Single model provider: **Gemini**.

**▶ Live demo: https://ortograph.pages.dev**

- **Input:** a multi-view orthographic drawing (PNG/JPG).
- **Output:** an editable **STEP** (+ STL) model with an automatic, pass/fail **dimension report**.
- **Engine:** one Gemini conversation runs the whole loop — analyze → generate → run → render → verify → refine.

---

## Why it's hard (and why verification is the point)

Inferring one solid that is consistent across three views is genuine spatial reasoning, and vision
models are weak at it. A part that *looks* right but *measures* wrong is useless as a replacement
part. So **checking is the product, not an afterthought** — and we check three independent ways:

| Signal | What it asks | How |
|---|---|---|
| **Eye** | Does it look like the part? | A vision critique compares the 4 rendered views to the drawing (structural errors only). |
| **Judge** | Would a fresh reviewer agree? | A separate, stronger model with **no system prompt and no history**, shown only the drawing + renders, vetoes false positives the in-context critic rationalizes. |
| **Ruler** | Does it measure right? | A deterministic **dimension gate** measures the B-rep (bbox, hole diameters, hole patterns: count / pitch / bolt-circle) against the drawing's callouts. |

A model is **verified** only when all three agree. The dimension gate is the differentiator — the
eye can be fooled, the ruler cannot.

---

## How it works

One `CadAgent` drives a single Gemini conversation:

1. **Analyze** — Gemini reads the drawing into a structured `Analysis` (summary, per-view notes, and
   a **dimension table** that becomes the ground truth for the gate).
2. **Generate** — it writes **CadQuery** code, grounded by an embedded CadQuery manual and a few
   examples fetched live via **Tavily**. Complex parts are built **one feature at a time** (staged
   build), each stage locked once it renders.
3. **Run + repair** — the untrusted script runs in a **sandboxed subprocess**; code errors are fed
   back and fixed before any verification.
4. **Render + measure** — export STEP/STL, render 4 views (front/top/side/iso), and measure the B-rep.
5. **Verify** — the three signals above.
6. **Refine** — if a check fails, the discrepancies are fed back and the model edits the *best
   working script so far* (minimal change, not a rewrite). Bounded iterations with **elitism** — it
   always returns the best candidate, never a regression.

Each run is saved to a timestamped `renders/run_<ts>/` with every iteration's artifacts and a full
`trace.md` of the model's reasoning and critiques. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Repo layout

```
.
├── backend/                 # the agent + CAD pipeline (Python)
│   ├── llm/gemini.py        #   Gemini access: ask / ask_code / ask_json / Conversation
│   ├── cad/                 #   sandboxed CadQuery runner
│   │   ├── render.py        #     render_file/_code -> STEP/STL/SVG + 4 views + measurements
│   │   └── _harness.py      #     runs untrusted code in a subprocess; measures the B-rep
│   └── agent/               #   the loop
│       ├── agent.py         #     CadAgent: analyze->generate->run->render->verify->refine
│       ├── analysis.py      #     drawing -> Analysis + dimension table
│       ├── gate.py          #     dimension gate (the "ruler")
│       ├── models.py        #     pydantic: Analysis, Dimension, BuildPlan
│       ├── prompts.py       #     all prompts (system, critique, judge, refine, staged)
│       ├── retrieval.py     #     optional Tavily CadQuery-example retrieval
│       └── cadquery_reference.md  # the embedded CadQuery manual
├── frontend/                # React (TanStack Start) demo app — the Ortograph UI
│   ├── src/{routes,components,demo}/
│   ├── public/demo/         #   bundled real-run artifacts the demo replays
│   └── scripts/bake_gate.py
├── docs/                    # ARCHITECTURE, AGENTS, SECURITY, views-reference, demo-script
├── samples/                 # sample engineering drawings
├── environment.yml          # conda env (Python 3.12 + CadQuery/OpenCASCADE)
├── pyproject.toml           # package + pinned deps
└── renders/                 # (gitignored) per-run outputs + trace.md
```

---

## Setup & run — backend

Needs a Google AI Studio API key (https://aistudio.google.com/apikey). CadQuery ships native
OpenCASCADE libraries, so the env is created via **conda**.

```bash
conda env create -f environment.yml
conda activate drawing-to-3d
pip install -e .[dev]            # add ,retrieval for the optional Tavily integration

cp .env.example .env             # then set GEMINI_API_KEY=... (and optionally TAVILY_API_KEY=...)
```

Run the agent on a drawing:

```bash
python -m backend.agent samples/orthographic_3/cad-drawing.png
#   --staged / --no-staged        force feature-by-feature vs one-shot (default: auto by complexity)
#   --thinking minimal|low|medium|high|dynamic
```

Outputs land in `renders/run_<timestamp>/` — open `final.html` (3D viewer), inspect `final.step`,
and read `trace.md`. Other entry points: `python -m backend.cad <script.py>` (render a CadQuery
script) and `python -m backend.llm` (Gemini smoke test).

## Setup & run — frontend (demo UI)

The web app is a guided demo that **replays real runs** from bundled artifacts (it is not wired to
the live backend yet; the data layer has a clean seam to add one). React + TanStack Start + Vite.

```bash
cd frontend
npm install            # or: bun install
npm run dev            # http://localhost:8080
```

The demo lets you pick a sample part, watch it reconstruct (staged animation), inspect the 3D STEP
model, see the live dimension-gate table, and download the STEP/STL.

### Deploy (Cloudflare Pages)

The frontend builds to a **static SPA** (`vite.config.ts` enables SPA mode; `postbuild` writes
`index.html`/`404.html` from the shell, and `public/_redirects` handles client-side routing). It's
hosted on Cloudflare Pages at **https://ortograph.pages.dev**.

To (re)deploy — needs a free Cloudflare account; no API key, the first run authorizes via browser:

```bash
cd frontend
npx wrangler login                                              # one-time browser auth
npm run build                                                   # -> dist/client (static)
npx wrangler pages deploy dist/client --project-name=ortograph  # uploads; prints the URL
```

`ortograph.pages.dev` always points to the latest deploy (the per-deployment `*.pages.dev` hash URLs
are previews and may show a TLS warning for a few minutes until their cert provisions — use the
production URL).

---

## Security

The pipeline executes **LLM-generated CadQuery code**, which is arbitrary code execution — the
single biggest risk. It is run **only** in a sandboxed subprocess with a scrubbed environment (no
secrets inherited), a hard timeout, and gitignored scratch output. Generated code is never `exec`'d
in the app process. Full threat model in [`docs/SECURITY.md`](docs/SECURITY.md).

---

## Scope (honest)

We win by reconstructing a few real part classes end-to-end with a **passing dimension table**, not
by gesturing at every possible part. The backend runs the full loop today (verified on a
multi-flange manifold and a staged mounting bracket). Clearest next steps: measure more dimension
kinds (thickness, feature spacing), and wire the frontend to the live backend (an `ApiRunner`
behind the existing `DrawingRunner` interface).

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the pipeline, verification, and roadmap
- [`docs/AGENTS.md`](docs/AGENTS.md) — conventions for AI coding agents working in this repo
- [`docs/SECURITY.md`](docs/SECURITY.md) — threat model and as-built status
- [`docs/views-reference.md`](docs/views-reference.md) — reference of technical-drawing view types
- [`docs/demo-script.md`](docs/demo-script.md) — the 60-second demo narration
