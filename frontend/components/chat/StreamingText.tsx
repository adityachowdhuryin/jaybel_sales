export function StreamingText({
  content,
  streaming,
}: {
  content: string;
  streaming?: boolean;
}) {
  return (
    <div className="text-sm whitespace-pre-wrap leading-relaxed">
      {content || (streaming ? "…" : "")}
      {streaming && (
        <span className="inline-block w-2 h-4 ml-0.5 bg-brand-500/80 animate-pulse align-middle" />
      )}
    </div>
  );
}
