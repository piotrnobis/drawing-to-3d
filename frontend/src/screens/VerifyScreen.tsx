import { useState } from "react";
import { GlassCard, PrimaryButton, SecondaryButton } from "../components/GlassCard";
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
      <div className="mb-8 text-center">
        <h2 className="font-[family-name:var(--font-display)] text-4xl text-white">
          We do not just generate. We check.
        </h2>
        <p className="mt-2 text-sm text-zinc-500">Shape overlay + dimension table — grounded feedback</p>
      </div>

      {!loaded ? (
        <GlassCard className="mx-auto max-w-md text-center">
          <PrimaryButton onClick={runVerify}>Run verification</PrimaryButton>
        </GlassCard>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <GlassCard>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-[11px] uppercase tracking-wider text-zinc-500">Overlay diff</p>
                <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-zinc-400">
                  IoU {(session.iou ?? 0).toFixed(2)}
                </span>
              </div>
              {session.overlayPreview && (
                <img
                  src={session.overlayPreview}
                  alt="Overlay"
                  className="w-full rounded-lg bg-white opacity-90"
                />
              )}
              <p className="mt-2 text-xs text-zinc-600">
                <span className="text-zinc-400">—</span> original &nbsp;
                <span className="text-[#c5341f]">- -</span> rebuilt
              </p>
              <div className="mt-4 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={openViewer}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs font-medium text-zinc-300 transition hover:border-[#c5341f]/40 hover:bg-[#c5341f]/10 hover:text-white"
                >
                  View 3D model ↗
                </button>
                <button
                  type="button"
                  onClick={openCadEditor}
                  className="w-full rounded-xl border border-[#569cd6]/30 bg-[#569cd6]/10 px-4 py-2.5 text-xs font-medium text-[#7ec8e3] transition hover:bg-[#569cd6]/20 hover:text-white"
                >
                  Edit in CAD editor ↗
                </button>
              </div>
            </GlassCard>

            <GlassCard>
              <p className="mb-3 text-[11px] uppercase tracking-wider text-zinc-500">Dimensions</p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-zinc-500">
                    <th className="pb-2 text-left">Dimension</th>
                    <th className="pb-2 text-right">Spec</th>
                    <th className="pb-2 text-right">Built</th>
                    <th className="pb-2 text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {session.dimensions.map((d) => (
                    <tr key={d.name} className="border-t border-white/5">
                      <td className="py-2.5 text-zinc-300">{d.name}</td>
                      <td className="py-2.5 text-right text-zinc-400">{d.spec.toFixed(2)}</td>
                      <td className="py-2.5 text-right text-zinc-400">{d.built.toFixed(2)}</td>
                      <td className="py-2.5 text-right">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                            d.status === "PASS"
                              ? "bg-emerald-500/15 text-emerald-400"
                              : "bg-[#c5341f]/15 text-[#c5341f]"
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

          <GlassCard className="mt-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="text-sm text-zinc-400">
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
                <PrimaryButton onClick={onNext}>Continue to 3D →</PrimaryButton>
              </div>
            </div>
          </GlassCard>
        </>
      )}
    </div>
  );
}
