import { useEffect, useState } from "react";
import { GlassCard } from "../components/GlassCard";

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
      <div className="mb-8 text-center">
        <h2 className="font-[family-name:var(--font-display)] text-4xl text-white">Building…</h2>
        <p className="mt-2 text-sm text-zinc-500">Turning your spec into parametric solid geometry</p>
      </div>

      <GlassCard className="space-y-4">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-3">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                step > i ? "bg-[#c5341f]/20 text-[#c5341f]" : "bg-white/5 text-zinc-600"
              }`}
            >
              {step > i ? "✓" : i + 1}
            </span>
            <span className={step > i ? "text-zinc-300" : "text-zinc-600"}>{label}</span>
            {step === i + 1 && step <= STEPS.length && (
              <span className="ml-auto h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white" />
            )}
          </div>
        ))}
      </GlassCard>
    </div>
  );
}
