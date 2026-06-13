import { GlassCard, PrimaryButton, SecondaryButton } from "../components/GlassCard";
import { PageHeader } from "../components/PageHeader";

interface Props {
  onRestart: () => void;
}

export function ExportScreen({ onRestart }: Props) {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <PageHeader
        label="Export"
        title="Ready to manufacture"
        subtitle="Editable B-rep, dimension-checked, exportable"
      />

      <GlassCard className="space-y-0 divide-y divide-[var(--color-border)]">
        {[
          { label: "STEP model", desc: "Editable parametric solid for CAD", ext: ".step" },
          { label: "glTF preview", desc: "Web 3D viewer format", ext: ".glb" },
          { label: "Dimension report", desc: "Pass/fail table + overlay snapshots", ext: ".pdf" },
        ].map((item) => (
          <div key={item.label} className="flex items-center justify-between py-5 first:pt-0 last:pb-0">
            <div>
              <p className="text-sm text-[var(--color-ink)]">{item.label}</p>
              <p className="mt-0.5 text-xs text-[var(--color-muted)]">{item.desc}</p>
            </div>
            <button
              type="button"
              className="border border-[var(--color-border)] bg-white px-4 py-2 text-xs tracking-wide text-[var(--color-ink)] transition hover:border-[var(--color-ink)]"
            >
              Download {item.ext}
            </button>
          </div>
        ))}

        <div className="grid gap-3 pt-6 sm:grid-cols-2">
          <SecondaryButton onClick={onRestart}>Start new drawing</SecondaryButton>
          <PrimaryButton>Open in external CAD ↗</PrimaryButton>
        </div>
      </GlassCard>
    </div>
  );
}
