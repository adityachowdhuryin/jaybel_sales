export function SummaryCard({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-xl border border-[var(--border)] bg-[var(--surface-0)] p-4 shadow-sm ${className}`}
    >
      <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">{title}</h3>
      {children}
    </section>
  );
}
