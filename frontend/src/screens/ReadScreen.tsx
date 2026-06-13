import { useState } from "react";
import { GlassCard, PrimaryButton, SecondaryButton } from "../components/GlassCard";
import { PageHeader } from "../components/PageHeader";
import type { DimensionRow, SessionState } from "../types";

interface Props {
  session: SessionState;
  onUpdate: (patch: Partial<SessionState>) => void;
  onNext: () => void;
  onRefine?: (feedback: string) => void;
}

const MOCK_DIMS: DimensionRow[] = [
  { name: "Overall height", spec: 60, built: 60, status: "PASS" },
  { name: "Overall width", spec: 60, built: 60, status: "PASS" },
  { name: "Wall thickness", spec: 18, built: 18, status: "PASS" },
  { name: "Bore Ø", spec: 12, built: 12, status: "PASS" },
];

function refineDimensions(dims: DimensionRow[], feedback: string): DimensionRow[] {
  const lower = feedback.toLowerCase();
  const nums = feedback.match(/\d+\.?\d*/g)?.map(Number) ?? [];
  const next = nums[0];

  return dims.map((d) => {
    const name = d.name.toLowerCase();
    if (next !== undefined) {
      if ((lower.includes("bore") || lower.includes("ø") || lower.includes("diameter")) && name.includes("bore")) {
        return { ...d, spec: next, built: next };
      }
      if ((lower.includes("wall") || lower.includes("thickness")) && name.includes("wall")) {
        return { ...d, spec: next, built: next };
      }
      if (lower.includes("height") && name.includes("height")) {
        return { ...d, spec: next, built: next };
      }
      if (lower.includes("width") && name.includes("width")) {
        return { ...d, spec: next, built: next };
      }
    }
    return d;
  });
}

export function ReadScreen({ session, onUpdate, onNext, onRefine }: Props) {
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [read, setRead] = useState(!!session.reconstructedPreview);
  const [revision, setRevision] = useState(session.iteration || 1);
  const [status, setStatus] = useState<string | null>(null);

  const runRead = async () => {
    setLoading(true);
    setStatus(null);
    await new Promise((r) => setTimeout(r, 1400));
    onUpdate({
      reconstructedPreview: session.imagePreview,
      svgPreview: session.imagePreview,
      dimensions: MOCK_DIMS,
      iteration: 1,
    });
    setRead(true);
    setRevision(1);
    setLoading(false);
  };

  const handleRefine = async () => {
    const note = feedback.trim();
    if (!note) {
      setStatus("Add feedback above before regenerating.");
      return;
    }

    setLoading(true);
    setStatus(null);
    onRefine?.(note);

    await new Promise((r) => setTimeout(r, 1200));

    const nextRevision = revision + 1;
    const refinedDims = refineDimensions(
      session.dimensions.length ? session.dimensions : MOCK_DIMS,
      note,
    );

    onUpdate({
      dimensions: refinedDims,
      iteration: nextRevision,
      reconstructedPreview: session.imagePreview,
      svgPreview: session.imagePreview,
    });

    setRevision(nextRevision);
    setFeedback("");
    setStatus(`Read v${nextRevision} — regenerated with your feedback.`);
    setLoading(false);
  };

  return (
    <div className="mx-auto w-full max-w-5xl">
      <PageHeader
        label="Review"
        title="What did we read?"
        subtitle="Gemini extracts an SVG reconstruction and structured spec. You review before we build."
      />

      {!read ? (
        <GlassCard className="mx-auto max-w-lg text-center">
          <p className="mb-6 text-sm text-[var(--color-muted)]">Ready to send your drawing to Gemini</p>
          <PrimaryButton onClick={runRead} loading={loading}>
            Extract spec & SVG
          </PrimaryButton>
        </GlassCard>
      ) : (
        <div className="grid gap-px border border-[var(--color-border)] bg-[var(--color-border)] md:grid-cols-3">
          <GlassCard className="border-0">
            <p className="label-spaced mb-4">Original</p>
            {session.imagePreview && (
              <img src={session.imagePreview} alt="Original" className="w-full bg-white" />
            )}
          </GlassCard>
          <GlassCard className="border-0">
            <div className="mb-4 flex items-center justify-between">
              <p className="label-spaced">Reconstructed</p>
              <span className="text-[10px] tracking-widest text-[var(--color-muted)]">v{revision}</span>
            </div>
            {session.reconstructedPreview && (
              <img src={session.reconstructedPreview} alt="Reconstructed" className="w-full bg-white" />
            )}
          </GlassCard>
          <GlassCard className="border-0">
            <p className="label-spaced mb-4">Dimensions</p>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[var(--color-muted)]">
                  <th className="pb-3 text-left font-medium">Dim</th>
                  <th className="pb-3 text-right font-medium">Spec</th>
                </tr>
              </thead>
              <tbody>
                {session.dimensions.map((d) => (
                  <tr key={d.name} className="border-t border-[var(--color-border)]">
                    <td className="py-2.5 text-[var(--color-ink)]">{d.name}</td>
                    <td className="py-2.5 text-right text-[var(--color-muted)]">{d.spec}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </GlassCard>
        </div>
      )}

      {read && (
        <GlassCard className="mt-8 space-y-5">
          <label className="label-spaced block">Something wrong? Tell us what to fix</label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Bore should be Ø12 not Ø10, wall is 18 mm…"
            rows={2}
            className="w-full resize-none border border-[var(--color-border)] bg-white px-4 py-3 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-muted)]/60 outline-none focus:border-[var(--color-border-strong)]"
          />
          {status && (
            <p
              className={`text-xs ${status.includes("Add feedback") ? "text-[var(--color-flag)]" : "text-[var(--color-pass)]"}`}
            >
              {status}
            </p>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            <SecondaryButton onClick={handleRefine} loading={loading} disabled={!feedback.trim()}>
              Regenerate read
            </SecondaryButton>
            <PrimaryButton onClick={onNext} disabled={loading}>
              Looks right — build CAD
            </PrimaryButton>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
