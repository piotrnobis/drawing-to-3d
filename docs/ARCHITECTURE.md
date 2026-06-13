# Architecture

The design we are building toward, in small steps. Read this so we all share one mental model.

## Goal and the hard constraint

Take a multi-view orthographic engineering drawing and reconstruct it as an **editable parametric CAD model** (STEP, a real B-rep with a feature tree), then **validate it dimensionally**.

The output must be parametric, **not a mesh**. A generated triangle soup looks fine and is useless: you cannot edit a wall thickness or re-fit a bore on it. This is the whole point of the Kyrall track.

## Why it is hard (and why we validate)

- Inferring a single solid that is consistent across three views is genuine spatial reasoning, and off-the-shelf vision models are weak at it.
- A part that *looks* right but *measures* wrong is worthless for a replacement part.

So verification is not a nice-to-have; it is the core of the project.

---

## Implementation status (where the code is today)

The repo currently implements a working slice of the loop, not all 10 stages:

- **`backend/agent` (`CadAgent`)** covers **generate (4)** + **repair (5)** today: it
  prompts Gemini (with a CadQuery few-shot reference) for code, runs it, and on
  failure feeds the traceback back into the *same* `Conversation` and retries.
- **`backend/cad`** covers part of **export (9)**: the sandboxed runner writes
  STEP + STL + SVG and a self-contained three.js HTML viewer. `RenderResult`
  (`ok`, `outputs`, `stdout`, `stderr`) is today's stand-in for the **runner-result
  contract** below — when we formalize it, `ok`→`success`, `outputs["step"]`→
  `step_path`, a future `outputs["gltf"]`→`gltf_path`, `stderr`→`error_trace`,
  and `measurements` get added by the validate stage.
- **`backend/llm`** is the Gemini access layer used by the agent.

**Not built yet:** extract → `DrawingSpec` (2), review (3), project/compare/refine
(6–8), the dimensional **validation gate**, glTF export, FastAPI, and the frontend.
These are the open lanes to pick up.

## The pipeline (10 stages, 4 phases)

**Phase A — Read**
1. **ingest** — load and validate the uploaded drawing image.
2. **extract** — Gemini → a structured `DrawingSpec` (views, dimensions, features, projection convention, units).
3. **review** *(optional human checkpoint)* — show the extracted spec as an annotated overlay on the drawing; a human can verify/edit before we build. Also runs fully automatic.

**Phase B — Build**
4. **generate** — `DrawingSpec` → CadQuery code, constrained to a real CAD vocabulary (sketch → extrude / revolve / hole / fillet / chamfer / boolean).
5. **repair** *(inner loop)* — execute the code; on syntax/kernel errors, feed the traceback back and regenerate. Max ~3 tries. No rendering here.

**Phase C — Verify**
6. **project** — project the solid back to orthographic views via hidden-line removal (CadQuery SVG export / OCC HLR), same convention as the input (default **first-angle / European**).
7. **compare** — register the projection against the input *geometry* per view; compute contour IoU + Chamfer distance + a color-coded diff overlay. Compare geometry-to-geometry (strip dimension lines, text, title block); never against the raw annotated drawing.
8. **refine** *(outer loop)* — feed the model the diff overlay + the failing dimensions, ask for a corrected part, re-check.

**Phase D — Export**
9. **export** — write **STEP**; also tessellate to **glTF/GLB** for the web viewer.
10. **preview** — UI shows the model + the dimension report.

---

## Verification = two signals

This is the differentiator. Keep both.

- **Shape (project-back overlay):** re-draw the solid as an orthographic line drawing and overlay it on the original; mismatches in outline, holes, and steps light up. This **localizes** where the part is wrong.
- **Size (dimensional table):** query the actual B-rep (bounding box, edge lengths, hole diameters, face-to-face distances) and check each callout against the spec within tolerance. This is the **hard gate** and the on-screen demo artifact.

The overlay catches feature/topology errors the table cannot see; the table catches scale errors the overlay smooths over.

## The refine loop (bounded on purpose)

```
generate → project → compare → pass? ──► export
   ▲                              │
   └───── grounded feedback ◄─────┘   (overlay image + failing dimensions)
```

- **Inner loop = repair** (cheap): fix code that won't run, from the error itself.
- **Outer loop = refine** (semantic): fix a valid-but-wrong shape, from the visual + dimensional feedback.
- **Max ~3 outer iterations.** Self-refinement plateaus fast.
- **Plateau guard:** stop if the score does not improve for 2 iterations; consider a fresh best-of-N regeneration instead of re-prompting the same chain.
- **Keep best (elitism):** always retain the highest-scoring candidate; never return a regression.

## Scope (be honest)

We win by nailing a few real part classes end-to-end (**extrude, revolve, holes, fillets/chamfers**) with a passing dimension table, not by gesturing at every possible part. Natural-language edits to the finished model are a **stretch goal**, gated behind a working core.

---

## The three interface contracts

Lock these **together** before building pieces. They let each lane work against stubs in parallel.

### 1. `DrawingSpec` (pydantic) — output of `extract`, input of `generate` + `validate`
- `units` (e.g. "mm"), `projection` ("first_angle" | "third_angle")
- `views[]`: name (front/top/side/section/iso), 2D contours
- `dimensions[]`: `value`, `tolerance`, and **what geometry it constrains** (the association is the point)
- `features[]`: holes (Ø, depth, counterbore/countersink), threads (e.g. M8×1.25), fillets/chamfers (R/C), material, title-block fields

### 2. Runner result — the seam between the model side and the CAD side
- **in:** a CadQuery code string
- **out:** `{ success, step_path, gltf_path, measurements, error_trace }`
- Generated code is executed **only** through the sandboxed runner (see `SECURITY.md`).

### 3. `PipelineResult` — what the API returns to the UI
- `spec`, `generated_code`, per-view `iou`, `overlay_image_urls`, `dimension_table[]` (name, spec, measured, status), `step_url`, `gltf_url`, `stage_status[]`

---

## Key prior art (for grounding, not copying)

- **CADCodeVerify / 3D-Premise / Seek-CAD** — VLM + CadQuery + visual refinement loops (this is our lineage).
- **CAD2Program** — VLM fine-tuned on engineering drawings (shows the pure-VLM route needs heavy domain data; we lean on validation instead).
- **DeepCAD / Text2CAD (NeurIPS 2024)** — the sketch→extrude command vocabulary we constrain generation to; DeepCAD is also a corpus we can mine for few-shot examples.