import { useState } from "react";
import { GlassCard, PrimaryButton, SecondaryButton } from "../components/GlassCard";
import type { SessionState } from "../types";

interface Props {
  session: SessionState;
  onUpdate: (patch: Partial<SessionState>) => void;
  onNext: () => void;
  onRefine: (feedback: string) => void;
}

const MOCK_DIMS = [
  { name: "Overall height", spec: 60, built: 60, status: "PASS" as const },
  { name: "Overall width", spec: 60, built: 60, status: "PASS" as const },
  { name: "Wall thickness", spec: 18, built: 18, status: "PASS" as const },
  { name: "Bore Ø", spec: 12, built: 12, status: "PASS" as const },
];

export function ReadScreen({ session, onUpdate, onNext, onRefine }: Props) {
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [read, setRead] = useState(!!session.reconstructedPreview);

  const runRead = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1400));
    onUpdate({
      reconstructedPreview: session.imagePreview,
      svgPreview: session.imagePreview,
      dimensions: MOCK_DIMS,
    });
    setRead(true);
    setLoading(false);
  };

  const handleRefine = async () => {
    if (!feedback.trim()) return;
    setLoading(true);
    onRefine(feedback);
    await new Promise((r) => setTimeout(r, 1200));
    setFeedback("");
    setLoading(false);
  };

  return (
    <div className="mx-auto w-full max-w-5xl">
      <div className="mb-8 text-center">
        <h2 className="font-[family-name:var(--font-display)] text-4xl text-white">
          What did we read?
        </h2>
        <p className="mt-2 text-sm text-zinc-500">
          Gemini extracts an SVG reconstruction + structured spec. You review before we build.
        </p>
      </div>

      {!read ? (
        <GlassCard className="mx-auto max-w-lg text-center">
          <p className="mb-4 text-sm text-zinc-400">Ready to send your drawing to Gemini</p>
          <PrimaryButton onClick={runRead} loading={loading}>
            Extract spec & SVG
          </PrimaryButton>
        </GlassCard>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <GlassCard>
            <p className="mb-3 text-[11px] uppercase tracking-wider text-zinc-500">Original</p>
            {session.imagePreview && (
              <img src={session.imagePreview} alt="Original" className="w-full rounded-lg bg-white" />
            )}
          </GlassCard>
          <GlassCard>
            <p className="mb-3 text-[11px] uppercase tracking-wider text-zinc-500">
              Reconstructed SVG → PNG
            </p>
            {session.reconstructedPreview && (
              <img
                src={session.reconstructedPreview}
                alt="Reconstructed"
                className="w-full rounded-lg bg-white"
              />
            )}
          </GlassCard>
          <GlassCard>
            <p className="mb-3 text-[11px] uppercase tracking-wider text-zinc-500">Dimensions</p>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-zinc-500">
                  <th className="pb-2 text-left font-medium">Dim</th>
                  <th className="pb-2 text-right font-medium">Spec</th>
                </tr>
              </thead>
              <tbody>
                {session.dimensions.map((d) => (
                  <tr key={d.name} className="border-t border-white/5">
                    <td className="py-2 text-zinc-300">{d.name}</td>
                    <td className="py-2 text-right text-zinc-400">{d.spec}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </GlassCard>
        </div>
      )}

      {read && (
        <GlassCard className="mt-4 space-y-4">
          <label className="block text-xs font-medium uppercase tracking-wider text-zinc-500">
            Something wrong? Tell us what to fix
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Bore should be Ø12 not Ø10, wall is 18 mm…"
            rows={2}
            className="w-full resize-none rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none"
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <SecondaryButton onClick={handleRefine}>Regenerate read</SecondaryButton>
            <PrimaryButton onClick={onNext}>Looks right — build CAD →</PrimaryButton>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
