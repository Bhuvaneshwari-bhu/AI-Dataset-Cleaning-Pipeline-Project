import EmptyState from '../ui/EmptyState';

export default function CleaningLog({ cleanLog = [] }) {
  if (!cleanLog.length) {
    return (
      <EmptyState
        title="No cleaning steps performed"
        description="Dataset required no transformations."
        className="py-6"
      />
    );
  }

  return (
    <ol className="space-y-2">
      {cleanLog.map((entry, i) => (
        <li key={i} className="flex items-start gap-3 text-sm">
          <span className="w-5 h-5 rounded-full bg-maroon-600/20 text-maroon-400 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 border border-maroon-600/20">
            {i + 1}
          </span>
          <span className="text-ink-secondary">{entry}</span>
        </li>
      ))}
    </ol>
  );
}
