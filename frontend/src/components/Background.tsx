export function Background() {
  return (
    <div className="pointer-events-none fixed inset-0" aria-hidden>
      <div className="absolute inset-0 bg-[var(--color-surface)]" />
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(154,139,122,0.08) 0%, transparent 70%)",
        }}
      />
    </div>
  );
}
