import { useEffect, useState } from "react";
import { GlassCard } from "../components/GlassCard";
import { PageHeader } from "../components/PageHeader";

interface Props {
  onDone: () => void;
}

const STEPS = [
  "Generating CadQuery from spec…",
  "Executing OpenCASCADE kernel…",
  "Repairing syntax errors…",
  "Projecting orthographic views…",
];

export function BuildScreen({ onDone }: Props) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timers = STEPS.map((_, i) =>
      setTimeout(() => {
        setStep(i + 1);
        if (i === STEPS.length - 1) setTimeout(onDone, 800);
      }, (i + 1) * 900),
    );
    return () => timers.forEach(clearTimeout);
  }, [onDone]);

  return (
    <div className="mx-auto w-full max-w-lg">
      <PageHeader
        label="Build"
        title="Building"
        subtitle="Turning your spec into parametric solid geometry"
      />

      <GlassCard className="space-y-5">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-4 border-b border-[var(--color-border)] pb-5 last:border-0 last:pb-0">
            <span
              className={`flex h-7 w-7 items-center justify-center text-xs ${
                step > i
                  ? "bg-[var(--color-ink)] text-[var(--color-surface-raised)]"
                  : "border border-[var(--color-border)] text-[var(--color-muted)]"
              }`}
            >
              {step > i ? "✓" : i + 1}
            </span>
            <span className={step > i ? "text-[var(--color-ink)]" : "text-[var(--color-muted)]"}>{label}</span>
            {step === i + 1 && step <= STEPS.length && (
              <span className="ml-auto h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-border)] border-t-[var(--color-ink)]" />
            )}
          </div>
        ))}
      </GlassCard>
    </div>
  );
}
