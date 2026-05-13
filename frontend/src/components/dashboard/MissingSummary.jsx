import EmptyState from '../ui/EmptyState';

export default function MissingSummary({ missingSummary = {}, typeIssues = [] }) {
  const missingEntries = Object.entries(missingSummary).sort((a, b) => b[1].count - a[1].count);

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-sm font-semibold text-ink-secondary mb-3">Missing Values by Column</h4>
        {missingEntries.length === 0 ? (
          <p className="text-sm text-success font-medium">✓ No missing values found</p>
        ) : (
          <div className="space-y-2.5">
            {missingEntries.map(([col, info]) => (
              <div key={col}>
                <div className="flex justify-between text-xs text-ink-secondary mb-1">
                  <span className="font-medium truncate">{col}</span>
                  <span className="ml-2 flex-shrink-0 text-ink-muted">{info.count} ({info.pct.toFixed(1)}%)</span>
                </div>
                <div className="w-full bg-white/[0.06] rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      info.pct > 20
                        ? 'bg-danger'
                        : info.pct > 5
                          ? 'bg-warning'
                          : 'bg-maroon-500'
                    }`}
                    style={{ width: `${Math.min(info.pct, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {typeIssues.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-ink-secondary mb-3">Type Issues</h4>
          <ul className="space-y-1.5">
            {typeIssues.map((issue, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-warning">
                <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
