# drawing-to-3d

**Reconstruct an editable parametric CAD model (STEP) from a technical engineering drawing.**

Munich AI Hackathon · Kyrall track. Working name: *drawing-to-3d* (rename freely).

- **Input:** a multi-view orthographic engineering drawing (PNG).
- **Output:** a parametric **STEP** model (editable B-rep, *not* a mesh), with an automatic dimension report.
- **Engine:** a single vision model (**Gemini 3.5 Flash**) driving extraction, code generation, and a verify/refine loop.

> **Status:** early. We build **incrementally**, one small piece at a time, with Claude Code as a copilot. Nothing here is a finished system yet; this README describes what we are building toward. See `ARCHITECTURE.md` for the design and `TASKS.md` for who owns what.

---

## How it works (one paragraph)

We read the drawing into a structured spec (views, dimensions, features), generate **CadQuery** code constrained to real CAD operations, then prove the result: project the solid back into orthographic views, overlay it against the original drawing, and measure every dimension against the spec. Mismatches are fed back to the model to refine. The dimensional pass/fail check is the hard gate and our differentiator. Full detail in [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Tech stack

| Area | Choice | Notes |
|---|---|---|
| Model | Gemini 3.5 Flash | via Google **AI Studio** key (Gemini Developer API) |
| Gemini SDK | `google-genai` | the unified SDK; **not** the deprecated `google-generativeai` |
| CAD kernel | **CadQuery** (OpenCASCADE) | B-rep, STEP export, orthographic projection, dimension queries |
| Backend | Python + FastAPI | *planned* |
| Frontend | React + Vite + TypeScript + Tailwind + react-three-fiber | *planned* |
| Tooling | ruff + black (py), eslint + prettier (ts) | keep deps lean and pinned |

We deliberately use **one** model provider and a **minimal** dependency set (smaller attack surface, cleaner security scan).

---

## Repo layout (current → target)

```
.
├── README.md              # this file
├── environment.yml        # ✅ conda env (python 3.12 + deps)
├── .env.example           # ✅ GEMINI_API_KEY=...
├── docs/
│   ├── ARCHITECTURE.md    # ✅ pipeline design + the 3 interface contracts
│   ├── AGENTS.md          # ✅ rules for Claude Code / AI agents working in this repo
│   └── SECURITY.md        # ✅ threat model, secrets, Aikido steps
├── backend/               # FastAPI + pipeline modules
│   ├── llm/
│   │   └── gemini.py      # ✅ Gemini helpers — ask / ask_code (JSON) / Conversation
│   ├── cad/               # ✅ sandboxed CadQuery runner + exporter (debug render)
│   │   ├── render.py      #    render_file / render_code -> STEP / STL / SVG / HTML
│   │   └── _harness.py    #    runs the untrusted script inside the subprocess
│   └── agent/             # ✅ drawing -> CadQuery -> render, self-refining loop
│       ├── agent.py       #    CadAgent: generate, render, refine on errors
│       ├── prompts.py     #    system prompt + refine prompt
│       └── cadquery_reference.md  # idiomatic CadQuery examples (model context)
├── renders/               # (gitignored) debug render outputs
├── samples/               # sample drawings + CadQuery fixtures
└── frontend/              # (planned) React UI
```

✅ = exists. Everything else lands as we build it.

---

## Setup

You need a Google AI Studio API key (https://aistudio.google.com/apikey).

```bash
# 1. clone + enter
git clone <repo> && cd drawing-to-3d

# 2. conda env (python 3.12 + CadQuery), then install the package
conda env create -f environment.yml
conda activate drawing-to-3d
pip install -e .[dev]

# 3. secrets — copy the example and paste your AI Studio key
cp .env.example .env
#   then edit .env:  GEMINI_API_KEY=your_key_here
```

## Run

```bash
# drawing -> CadQuery -> rendered model (STEP/STL/SVG + HTML viewer in renders/)
python -m backend.agent samples/orthographic_3/cad-drawing.png

# render a CadQuery script directly
python -m backend.cad samples/cad/bracket.py

# Gemini smoke test
python -m backend.llm
```

Frontend run instructions are added here as that part is built.

---

## Deliverables (hackathon submission)

- [ ] 2-minute demo video (Loom or similar)
- [ ] Public GitHub repo with this README + setup that works from scratch
- [ ] Aikido security report screenshot (see `SECURITY.md`)
- [ ] Working pipeline on 2–3 hero parts with a passing dimension table

---

## Docs index

- [`ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — the pipeline and the interface contracts
- [`AGENTS.md`](./docs/AGENTS.md) — how AI coding agents should work here
- [`SECURITY.md`](./docs/SECURITY.md) — threat model, secrets, Aikido
