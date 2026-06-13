import { GlassCard, PrimaryButton } from "../components/GlassCard";
import { PageHeader } from "../components/PageHeader";

interface Props {
  onNext: () => void;
}

const openViewer = () =>
  window.open("/viewer3d.html", "_blank", "noopener,noreferrer,width=1100,height=720");

export function PreviewScreen({ onNext }: Props) {
  return (
    <div className="mx-auto w-full max-w-4xl">
      <PageHeader
        label="Preview"
        title="Your 3D model"
        subtitle="Final model — inspect only, no further edits"
      />

      <GlassCard>
        <div className="mb-6 flex items-center justify-between border border-[var(--color-border)] bg-white px-5 py-4">
          <p className="text-sm text-[var(--color-muted)]">
            <span className="text-[var(--color-ink)]">Locked for export.</span> Edits were completed in
            Verify. This model is ready to ship.
          </p>
          <span className="shrink-0 text-[10px] tracking-[0.2em] uppercase text-[var(--color-pass)]">
            Final
          </span>
        </div>

        <button
          type="button"
          onClick={openViewer}
          className="relative flex aspect-[16/10] w-full cursor-pointer items-center justify-center overflow-hidden border border-[var(--color-border)] bg-[#eceae6] transition hover:border-[var(--color-border-strong)]"
        >
          <div
            className="h-40 w-40 opacity-60"
            style={{
              background: "linear-gradient(145deg, #d4cfc7 0%, #b8b2a8 100%)",
              clipPath:
                "polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%)",
            }}
          />
          <p className="absolute bottom-5 text-xs tracking-wide text-[var(--color-muted)]">
            Click to open full 3D viewer ↗
          </p>
        </button>

        <div className="mt-6">
          <PrimaryButton onClick={onNext}>Export</PrimaryButton>
        </div>
      </GlassCard>
    </div>
  );
}
