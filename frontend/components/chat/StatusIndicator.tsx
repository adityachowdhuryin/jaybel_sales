export function StatusIndicator({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p className="text-sm text-[var(--muted)] animate-pulse">{message}</p>
  );
}
