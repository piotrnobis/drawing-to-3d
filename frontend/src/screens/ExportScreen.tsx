import { GlassCard, PrimaryButton, SecondaryButton } from "../components/GlassCard";

interface Props {
  onRestart: () => void;
}

export function ExportScreen({ onRestart }: Props) {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="mb-8 text-center">
        <h2 className="font-[family-name:var(--font-display)] text-4xl text-white">
          Ready to manufacture
        </h2>
        <p className="mt-2 text-sm text-zinc-500">Editable B-rep, dimension-checked, exportable</p>
      </div>

      <GlassCard className="space-y-4">
        {[
          { label: "STEP model", desc: "Editable parametric solid for CAD", ext: ".step" },
          { label: "glTF preview", desc: "Web 3D viewer format", ext: ".glb" },
          { label: "Dimension report", desc: "Pass/fail table + overlay snapshots", ext: ".pdf" },
        ].map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between rounded-xl border border-white/5 bg-black/20 px-4 py-4"
          >
            <div>
              <p className="text-sm font-medium text-zinc-200">{item.label}</p>
              <p className="text-xs text-zinc-600">{item.desc}</p>
            </div>
            <button
              type="button"
              className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-zinc-300 transition hover:bg-white/10"
            >
              Download {item.ext}
            </button>
          </div>
        ))}

        <div className="grid gap-3 pt-2 sm:grid-cols-2">
          <SecondaryButton onClick={onRestart}>Start new drawing</SecondaryButton>
          <PrimaryButton>Open in external CAD ↗</PrimaryButton>
        </div>
      </GlassCard>
    </div>
  );
}
