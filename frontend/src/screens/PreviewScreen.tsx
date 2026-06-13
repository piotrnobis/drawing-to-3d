import { GlassCard, PrimaryButton } from "../components/GlassCard";

interface Props {
  onNext: () => void;
}

const openViewer = () =>
  window.open("/viewer3d.html", "_blank", "noopener,noreferrer,width=1100,height=720");

export function PreviewScreen({ onNext }: Props) {
  return (
    <div className="mx-auto w-full max-w-4xl">
      <div className="mb-8 text-center">
        <h2 className="font-[family-name:var(--font-display)] text-4xl text-white">Your 3D model</h2>
        <p className="mt-2 text-sm text-zinc-500">Final model — inspect only, no further edits</p>
      </div>

      <GlassCard>
        <div className="mb-4 flex items-center justify-between rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
          <p className="text-sm text-emerald-400/90">
            <span className="font-semibold">Locked for export.</span>{" "}
            <span className="text-emerald-400/70">Edits were completed in Verify. This model is ready to ship.</span>
          </p>
          <span className="shrink-0 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400">
            FINAL
          </span>
        </div>

        <button
          type="button"
          onClick={openViewer}
          className="relative flex aspect-video w-full cursor-pointer items-center justify-center overflow-hidden rounded-xl border border-white/5 bg-gradient-to-br from-zinc-900 to-black transition hover:border-white/15"
        >
          <div
            className="h-48 w-48 animate-float"
            style={{
              background:
                "linear-gradient(135deg, rgba(197,52,31,0.3) 0%, rgba(124,58,237,0.2) 50%, rgba(255,255,255,0.05) 100%)",
              clipPath:
                "polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%)",
            }}
          />
          <p className="absolute bottom-4 text-xs text-zinc-500">Click to open full 3D viewer ↗</p>
        </button>

        <div className="mt-5">
          <PrimaryButton onClick={onNext}>Export →</PrimaryButton>
        </div>
      </GlassCard>
    </div>
  );
}
