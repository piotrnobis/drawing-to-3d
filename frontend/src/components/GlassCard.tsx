interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
}

export function GlassCard({ children, className = "" }: GlassCardProps) {
  return (
    <div
      className={`rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-2xl shadow-black/40 backdrop-blur-xl ${className}`}
    >
      {children}
    </div>
  );
}

interface PrimaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export function PrimaryButton({ children, onClick, disabled, loading }: PrimaryButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className="group relative w-full overflow-hidden rounded-xl px-6 py-3.5 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-40"
    >
      <span
        className="absolute inset-0 bg-gradient-to-r from-[#c5341f] via-[#e11d48] to-[#7c3aed] transition group-hover:opacity-90"
        aria-hidden
      />
      <span className="relative flex items-center justify-center gap-2">
        {loading && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
        )}
        {children}
      </span>
    </button>
  );
}

export function SecondaryButton({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-xl border border-white/10 bg-white/5 px-6 py-3 text-sm font-medium text-zinc-300 transition hover:bg-white/10 hover:text-white"
    >
      {children}
    </button>
  );
}
