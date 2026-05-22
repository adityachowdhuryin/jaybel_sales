export function CostWarning({ bytes }: { bytes?: number }) {
  if (bytes == null || bytes <= 0) return null;
  const gb = bytes / 1e9;
  return (
    <p className="mt-2 text-xs text-amber-400/90 bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2">
      Large query scan: ~{gb.toFixed(2)} GB scanned (soft limit warning).
    </p>
  );
}
