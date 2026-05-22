function formatTime(iso?: string) {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return null;
  }
}

export function UserMessage({
  content,
  createdAt,
}: {
  content: string;
  createdAt?: string;
}) {
  const time = formatTime(createdAt);
  return (
    <div className="flex justify-end mb-4">
      <div>
        <div className="max-w-[85%] ml-auto rounded-2xl rounded-br-md bg-brand-600 px-4 py-2.5 text-sm text-white">
          {content}
        </div>
        {time && (
          <p className="text-[10px] text-[var(--muted)] text-right mt-1 pr-1">{time}</p>
        )}
      </div>
    </div>
  );
}
