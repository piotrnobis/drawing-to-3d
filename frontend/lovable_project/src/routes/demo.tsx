import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { StepViewer } from "@/components/StepViewer";
import { demoRuns } from "@/demo/runs";
import { demoRunner } from "@/demo/runner";
import type { DemoRun } from "@/demo/types";

export const Route = createFileRoute("/demo")({
  head: () => ({
    meta: [
      { title: "Demo — Ortograph" },
      { name: "description", content: "Watch Ortograph rebuild a 2D engineering drawing into a verified, editable 3D STEP model." },
      { property: "og:title", content: "Demo — Ortograph" },
      { property: "og:description", content: "A drawing in, a verified editable STEP model out." },
    ],
  }),
  component: DemoPage,
});

type Status = "idle" | "processing" | "ready" | "approved";

function DemoPage() {
  const [runId, setRunId] = useState<DemoRun["id"]>("bracket");
  const [status, setStatus] = useState<Status>("idle");
  const [currentStage, setCurrentStage] = useState(-1);
  const [stageLabel, setStageLabel] = useState("");
  const [stageIso, setStageIso] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const [editPrompt, setEditPrompt] = useState("");
  const [editing, setEditing] = useState(false);
  const [edits, setEdits] = useState<string[]>([]);
  const editTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const run = demoRuns.find((r) => r.id === runId) ?? demoRuns[0];

  useEffect(
    () => () => {
      abortRef.current?.abort();
      if (editTimer.current) clearTimeout(editTimer.current);
    },
    [],
  );

  function clearEdits() {
    if (editTimer.current) clearTimeout(editTimer.current);
    setEditPrompt("");
    setEditing(false);
    setEdits([]);
  }

  function selectRun(id: DemoRun["id"]) {
    if (id === runId) return;
    abortRef.current?.abort();
    setRunId(id);
    setStatus("idle");
    setCurrentStage(-1);
    setStageIso(null);
    clearEdits();
  }

  function start() {
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    setStatus("processing");
    setCurrentStage(-1);
    setStageIso(run.sourceDrawing);
    demoRunner
      .runDrawing({
        runId: run.id,
        stageMs: run.mode === "staged" ? 620 : 850,
        signal: ac.signal,
        onStage: (u) => {
          setCurrentStage(u.stageIndex);
          setStageLabel(u.label);
          if (u.isoUrl) setStageIso(u.isoUrl);
        },
      })
      .then(() => {
        if (ac.signal.aborted) return;
        setCurrentStage(run.stages.length);
        setStatus("ready");
      })
      .catch((e) => {
        if ((e as Error)?.name !== "AbortError") console.error(e);
      });
  }

  function reset() {
    abortRef.current?.abort();
    setStatus("idle");
    setCurrentStage(-1);
    setStageIso(null);
    clearEdits();
  }

  function applyEdit() {
    const text = editPrompt.trim();
    if (!text || editing) return;
    setEdits((e) => [...e, text]);
    setEditPrompt("");
    setEditing(true);
    if (editTimer.current) clearTimeout(editTimer.current);
    editTimer.current = setTimeout(() => setEditing(false), 1500);
  }

  async function download(url: string, ext: string) {
    const res = await fetch(url);
    const blob = await res.blob();
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = `ortograph_${run.id}.${ext}`;
    a.click();
    URL.revokeObjectURL(href);
  }

  const showModel = status === "ready" || status === "approved";

  return (
    <main className="wrap" style={{ paddingTop: 48, paddingBottom: 40 }}>
      <div className="eyebrow">Demo · drawing → verified editable solid</div>
      <h1 style={{ marginTop: 14 }}>Watch it rebuild a drawing.</h1>
      <p className="lead" style={{ marginTop: 14 }}>
        Ortograph reads a multi-view engineering drawing and reconstructs it as a real parametric STEP model — proving it right with shape, an independent judge, and measured dimensions. Pick a sample below and run it.
      </p>

      <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 22, flexWrap: "wrap" }}>
        <div className="seg">
          {demoRuns.map((r) => (
            <button key={r.id} className={r.id === runId ? "on" : ""} onClick={() => selectRun(r.id)}>
              {r.title}
              <span className="sub">{r.subtitle}</span>
            </button>
          ))}
        </div>
        <span className="hint mono" style={{ fontSize: 11.5, color: "var(--ink-soft)", letterSpacing: ".06em" }}>
          demo mode · replaying a real run
        </span>
      </div>

      <div className="demo-grid">
        <div>
          {!showModel ? (
            <>
              <div className="buildframe">
                <img src={stageIso ?? run.sourceDrawing} alt={status === "processing" ? stageLabel : "input drawing"} />
                <span className="flabel">
                  {status === "processing"
                    ? run.mode === "staged"
                      ? `stage ${currentStage + 1} · ${stageLabel}`
                      : stageLabel
                    : "input drawing"}
                </span>
                {status === "processing" && (
                  <span className="fcount">{Math.min(currentStage + 1, run.stages.length)} / {run.stages.length}</span>
                )}
              </div>

              {status === "idle" && (
                <div style={{ marginTop: 18, textAlign: "center" }}>
                  <button className="btn primary" onClick={start}>▶ Reconstruct</button>
                  <div className="hint" style={{ marginTop: 8 }}>{run.title} — {run.subtitle}</div>
                </div>
              )}

              {status === "processing" && (
                <div className="status-list">
                  {run.stages.map((s, i) => {
                    const state = i < currentStage ? "done" : i === currentStage ? "active" : "";
                    return (
                      <div key={s.index} className={"status-item " + state}>
                        <span className="dot" />
                        <span>{s.label}</span>
                        <span className="ts">{state === "done" ? "OK" : state === "active" ? "…" : ""}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            <>
              <div className="eyebrow" style={{ marginBottom: 10 }}>3D model · drag to rotate · scroll to zoom</div>
              <div className="viewer" style={{ padding: 0 }}>
                <span className="vlabel">ISO · final.step</span>
                <span className="vhint">drag · rotate</span>
                <StepViewer stepUrl={run.stepUrl} />
                {editing && (
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: "rgba(255,255,255,0.78)",
                      backdropFilter: "blur(2px)",
                      fontFamily: "IBM Plex Mono, monospace",
                      fontSize: 12,
                      letterSpacing: ".16em",
                      textTransform: "uppercase",
                      color: "var(--accent)",
                    }}
                  >
                    ↻ applying your change…
                  </div>
                )}
              </div>
              <div className="views-grid" style={{ gridTemplateColumns: "repeat(4,1fr)", marginTop: 12 }}>
                {(["front", "top", "side", "iso"] as const).map((v) => (
                  <figure key={v}>
                    <img src={run.views[v]} alt={`${v} view`} loading="lazy" />
                    <figcaption>{v}</figcaption>
                  </figure>
                ))}
              </div>
            </>
          )}
        </div>

        <aside className="sidepanel">
          <div className="panel-card">
            <h3>Actions</h3>
            <div className="btn-row">
              <button className="btn primary" disabled={status === "processing"} onClick={start}>
                {status === "idle" ? "▶ Reconstruct" : "↻ Run again"}
              </button>
              <button className="btn pass" disabled={status !== "ready"} onClick={() => setStatus("approved")}>✓ Approve</button>
              <button className="btn" disabled={!showModel} onClick={() => download(run.stepUrl, "step")}>↓ Download .step</button>
              <button className="btn" disabled={!showModel} onClick={() => download(run.stlUrl, "stl")}>↓ Download .stl</button>
              <button className="btn ghost" disabled={status === "idle"} onClick={reset}>✕ Reset</button>
            </div>
            <div className="mono" style={{ fontSize: 12, color: "var(--ink-soft)", lineHeight: 1.7, marginTop: 12 }}>
              <div>part: <span style={{ color: "var(--ink)" }}>{run.title}</span></div>
              <div>status: <span style={{ color: "var(--accent)" }}>{status.toUpperCase()}</span></div>
              <div>stages: {Math.max(0, Math.min(currentStage + (showModel ? 0 : 1), run.stages.length))}/{run.stages.length}</div>
            </div>
          </div>

          {showModel && (
            <div className="panel-card">
              <h3>Final tweak</h3>
              <p style={{ margin: "0 0 10px", fontSize: 12.5, color: "var(--ink-soft)", lineHeight: 1.5 }}>
                Describe any last change in plain language — Ortograph edits the parametric model before you export.
              </p>
              <textarea
                className="feedback"
                style={{ minHeight: 80 }}
                placeholder="e.g. round the base corners to R3 · widen the rib to 12 mm · add a chamfer on the top edge"
                value={editPrompt}
                onChange={(e) => setEditPrompt(e.target.value)}
              />
              <button
                className="btn primary"
                style={{ marginTop: 10, width: "100%" }}
                disabled={!editPrompt.trim() || editing}
                onClick={applyEdit}
              >
                {editing ? "↻ Applying…" : "✎ Apply edit"}
              </button>
              {edits.length > 0 && (
                <div className="mono" style={{ marginTop: 12, fontSize: 11.5, color: "var(--ink-soft)", lineHeight: 1.8 }}>
                  {edits.map((t, i) => (
                    <div key={i}>✓ <span style={{ color: "var(--ink)" }}>{t}</span></div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="panel-card">
            <h3>What it is</h3>
            <p style={{ margin: 0, fontSize: 14, color: "var(--ink-soft)", lineHeight: 1.55 }}>{run.summary}</p>
            <p style={{ margin: "10px 0 0", fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.5 }}>
              <b style={{ color: "var(--ink)" }}>Likely:</b> {run.guess}
            </p>
          </div>

          <div className="panel-card">
            <h3>Dimension gate</h3>
            {showModel ? (
              <>
                <div className="gate-scroll">
                  <table className="dim">
                    <thead>
                      <tr><th>dimension</th><th>target</th><th>built</th><th>status</th></tr>
                    </thead>
                    <tbody>
                      {run.gate.rows.map((r) => (
                        <tr key={r.label}>
                          <td>{r.label}</td>
                          <td className="r">{r.target}</td>
                          <td className="r">{r.measured ?? "—"}</td>
                          <td>
                            <span className={"pill " + (r.status === "pass" ? "pass" : r.status === "fail" ? "fail" : "na")}>
                              {r.status === "unmeasured" ? "N/A" : r.status.toUpperCase()}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="verdict"><b>{run.gate.verdict}</b></div>
              </>
            ) : (
              <p style={{ margin: 0, fontSize: 13, color: "var(--ink-soft)" }}>Runs once the model is built — every callout measured against the solid.</p>
            )}
          </div>
        </aside>
      </div>
    </main>
  );
}
