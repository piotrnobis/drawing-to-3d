import { STAGES, type Stage } from "../types";

interface HeaderProps {
  stage: Stage;
  onStageClick?: (stage: Stage) => void;
}

export function Header({ stage, onStageClick }: HeaderProps) {
  const idx = STAGES.findIndex((s) => s.id === stage);

  return (
    <header className="relative z-10 border-b border-[var(--color-border)]">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6 md:py-7">
        <button
          type="button"
          onClick={() => onStageClick?.("upload")}
          className="font-[family-name:var(--font-display)] text-xl tracking-tight text-[var(--color-ink)] transition hover:opacity-60"
        >
          Datum
        </button>

        <nav className="hidden items-center gap-8 md:flex">
          {STAGES.map((s, i) => {
            const active = s.id === stage;
            const done = i < idx;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => onStageClick?.(s.id)}
                className={`text-xs tracking-[0.15em] uppercase transition ${
                  active
                    ? "text-[var(--color-ink)]"
                    : done
                      ? "text-[var(--color-muted)] hover:text-[var(--color-ink)]"
                      : "text-[var(--color-border-strong)] hover:text-[var(--color-muted)]"
                }`}
              >
                {s.label}
              </button>
            );
          })}
        </nav>

        <span className="hidden text-[10px] tracking-[0.2em] uppercase text-[var(--color-muted)] sm:block">
          Munich · 2026
        </span>
      </div>
    </header>
  );
}
