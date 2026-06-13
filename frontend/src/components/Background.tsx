export function Background() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden>
      <div
        className="animate-pulse-glow absolute -left-32 top-[-10%] h-[520px] w-[520px] rounded-full opacity-60 blur-[120px]"
        style={{ background: "radial-gradient(circle, #7c3aed 0%, transparent 70%)" }}
      />
      <div
        className="animate-pulse-glow absolute right-[-8%] top-[20%] h-[480px] w-[480px] rounded-full opacity-50 blur-[110px]"
        style={{
          background: "radial-gradient(circle, #e11d48 0%, transparent 70%)",
          animationDelay: "2s",
        }}
      />
      <div
        className="animate-pulse-glow absolute bottom-[-15%] left-[30%] h-[400px] w-[600px] rounded-full opacity-40 blur-[100px]"
        style={{
          background: "radial-gradient(circle, #f59e0b 0%, transparent 70%)",
          animationDelay: "4s",
        }}
      />
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
    </div>
  );
}
