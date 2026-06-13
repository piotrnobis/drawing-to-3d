interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
}

export function GlassCard({ children, className = "" }: GlassCardProps) {
  return (
    <div
      className={`border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6 md:p-8 ${className}`}
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
      className="w-full border border-[var(--color-ink)] bg-[var(--color-ink)] px-6 py-3.5 text-sm font-medium tracking-wide text-[var(--color-surface-raised)] transition hover:bg-transparent hover:text-[var(--color-ink)] disabled:cursor-not-allowed disabled:opacity-35"
    >
      <span className="flex items-center justify-center gap-2">
        {loading && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-current/30 border-t-current" />
        )}
        {children}
      </span>
    </button>
  );
}

interface SecondaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export function SecondaryButton({ children, onClick, disabled, loading }: SecondaryButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className="w-full border border-[var(--color-border-strong)] bg-transparent px-6 py-3 text-sm font-medium tracking-wide text-[var(--color-ink)] transition hover:border-[var(--color-ink)] disabled:cursor-not-allowed disabled:opacity-35"
    >
      <span className="flex items-center justify-center gap-2">
        {loading && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-muted)]/30 border-t-[var(--color-ink)]" />
        )}
        {children}
      </span>
    </button>
  );
}
