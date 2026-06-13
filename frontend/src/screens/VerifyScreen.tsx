import { useState } from "react";
import { GlassCard, PrimaryButton, SecondaryButton } from "../components/GlassCard";
import { PageHeader } from "../components/PageHeader";
import type { SessionState } from "../types";

interface Props {
  session: SessionState;
  onUpdate: (patch: Partial<SessionState>) => void;
  onNext: () => void;
  onRefine: () => void;
}

const openCadEditor = () =>
  window.open("/cad-editor.html", "_blank", "noopener,noreferrer,width=1280,height=800");

const openViewer = () =>
  window.open("/viewer3d.html", "_blank", "noopener,noreferrer,width=1100,height=720");

export function VerifyScreen({ session, onUpdate, onNext, onRefine }: Props) {
  const [loaded, setLoaded] = useState(session.iou !== null);

  const runVerify = async () => {
    await new Promise((r) => setTimeout(r, 1000));
    onUpdate({
      overlayPreview: session.imagePreview,
      iou: 0.91,
      dimensions: [
        { name: "Overall height", spec: 60, built: 59.98, status: "PASS" },
        { name: "Overall width", spec: 60, built: 60.01, status: "PASS" },
        { name: "Wall thickness", spec: 18, built: 18.0, status: "PASS" },
        { name: "Bore Ø", spec: 12, built: 12.41, status: "FLAG" },
      ],
    });
    setLoaded(true);
  };

  const hasFlag = session.dimensions.some((d) => d.status === "FLAG");

  return (
    <div className="mx-auto w-full max-w-5xl">
      <PageHeader
        label="Verify"
        title="We do not just generate. We check."
        subtitle="Shape overlay and dimension table — grounded feedback"
      />

      {!loaded ? (
        <GlassCard className="mx-auto max-w-md text-center">
          <PrimaryButton onClick={runVerify}>Run verification</PrimaryButton>
        </GlassCard>
      ) : (
        <>
          <div className="grid gap-px border border-[var(--color-border)] bg-[var(--color-border)] md:grid-cols-2">
            <GlassCard className="border-0">
              <div className="mb-4 flex items-center justify-between">
                <p className="label-spaced">Overlay diff</p>
                <span className="text-xs text-[var(--color-muted)]">IoU {(session.iou ?? 0).toFixed(2)}</span>
              </div>
              {session.overlayPreview && (
                <img src={session.overlayPreview} alt="Overlay" className="w-full bg-white" />
              )}
              <p className="mt-3 text-xs text-[var(--color-muted)]">
                <span>—</span> original &nbsp;
                <span className="text-[var(--color-flag)]">- -</span> rebuilt
              </p>
              <div className="mt-5 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={openViewer}
                  className="w-full border border-[var(--color-border)] bg-white px-4 py-2.5 text-xs tracking-wide text-[var(--color-ink)] transition hover:border-[var(--color-ink)]"
                >
                  View 3D model ↗
                </button>
                <button
                  type="button"
                  onClick={openCadEditor}
                  className="w-full border border-[var(--color-border)] bg-white px-4 py-2.5 text-xs tracking-wide text-[var(--color-ink)] transition hover:border-[var(--color-ink)]"
                >
                  Edit in CAD editor ↗
                </button>
              </div>
            </GlassCard>

            <GlassCard className="border-0">
              <p className="label-spaced mb-4">Dimensions</p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-[var(--color-muted)]">
                    <th className="pb-3 text-left font-medium">Dimension</th>
                    <th className="pb-3 text-right font-medium">Spec</th>
                    <th className="pb-3 text-right font-medium">Built</th>
                    <th className="pb-3 text-right font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {session.dimensions.map((d) => (
                    <tr key={d.name} className="border-t border-[var(--color-border)]">
                      <td className="py-3 text-[var(--color-ink)]">{d.name}</td>
                      <td className="py-3 text-right text-[var(--color-muted)]">{d.spec.toFixed(2)}</td>
                      <td className="py-3 text-right text-[var(--color-muted)]">{d.built.toFixed(2)}</td>
                      <td className="py-3 text-right">
                        <span
                          className={`text-[11px] tracking-wider uppercase ${
                            d.status === "PASS" ? "text-[var(--color-pass)]" : "text-[var(--color-flag)]"
                          }`}
                        >
                          {d.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </GlassCard>
          </div>

          <GlassCard className="mt-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="text-sm text-[var(--color-muted)]">
                Iteration {session.iteration}/3
                {hasFlag && " — FLAG detected, refine recommended"}
              </p>
              <div className="flex flex-wrap gap-3">
                {hasFlag && (
                  <>
                    <SecondaryButton onClick={openCadEditor}>Edit in CAD editor ↗</SecondaryButton>
                    <SecondaryButton
                      onClick={() => {
                        onRefine();
                        onUpdate({ iteration: session.iteration + 1 });
                      }}
                    >
                      Refine with Gemini
                    </SecondaryButton>
                  </>
                )}
                <PrimaryButton onClick={onNext}>Continue to 3D</PrimaryButton>
              </div>
            </div>
          </GlassCard>
        </>
      )}
    </div>
  );
}
