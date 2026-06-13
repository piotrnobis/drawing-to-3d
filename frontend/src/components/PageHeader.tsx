interface PageHeaderProps {
  label?: string;
  title: string;
  subtitle?: string;
  centered?: boolean;
}

export function PageHeader({ label, title, subtitle, centered = true }: PageHeaderProps) {
  return (
    <div className={`mb-12 ${centered ? "text-center" : ""}`}>
      {label && <p className="label-spaced mb-5">{label}</p>}
      <h2 className="font-[family-name:var(--font-display)] text-4xl font-normal leading-[1.15] tracking-tight text-[var(--color-ink)] md:text-5xl">
        {title}
      </h2>
      {subtitle && (
        <p className={`mt-4 max-w-lg text-sm leading-relaxed text-[var(--color-muted)] ${centered ? "mx-auto" : ""}`}>
          {subtitle}
        </p>
      )}
    </div>
  );
}
