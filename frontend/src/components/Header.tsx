import { STAGES, type Stage } from "../types";

interface HeaderProps {
  stage: Stage;
  onStageClick?: (stage: Stage) => void;
}

export function Header({ stage, onStageClick }: HeaderProps) {
  const idx = STAGES.findIndex((s) => s.id === stage);

  return (
    <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-sm font-bold text-[#c5341f]">
          ◳
        </span>
        <span className="text-sm font-semibold tracking-[0.2em] text-zinc-300">DATUM</span>
      </div>

      <nav className="hidden items-center gap-1 md:flex">
        {STAGES.map((s, i) => {
          const active = s.id === stage;
          const done = i < idx;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => onStageClick?.(s.id)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                active
                  ? "bg-white/10 text-white"
                  : done
                    ? "text-zinc-400 hover:text-white"
                    : "text-zinc-600"
              }`}
            >
              {s.num} {s.label}
            </button>
          );
        })}
      </nav>

      <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] uppercase tracking-wider text-zinc-500">
        Kyrall · Hackathon
      </span>
    </header>
  );
}
