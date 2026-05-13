function Metric({ label, value, sub, icon, accent }) {
  const ACCENTS = {
    maroon: 'bg-maroon-600/15 text-maroon-400',
    success: 'bg-success/10 text-success',
    warning: 'bg-warning/10 text-warning',
    danger: 'bg-danger/10 text-red-400',
    purple: 'bg-purple-500/10 text-purple-400',
    muted: 'bg-white/[0.06] text-ink-muted',
  };

  return (
    <div className="bg-card border border-white/[0.08] rounded-2xl shadow-card p-5 flex items-center gap-4 hover:scale-[1.02] hover:shadow-glow-maroon-sm hover:border-maroon-600/30 transition-all duration-200 cursor-default">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${ACCENTS[accent]}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-2xl font-extrabold text-ink leading-none">{value}</p>
        <p className="text-xs font-medium text-ink-muted mt-1 truncate">{label}</p>
        {sub && <p className="text-xs text-ink-muted/70 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  );
}

export default function OverviewCards({ result }) {
  const {
    row_count_raw,
    row_count_clean,
    column_count,
    duplicate_count,
    total_outliers,
    missing_summary,
  } = result;

  const missingCols = Object.keys(missing_summary || {}).length;
  const rowsRemoved = row_count_raw - row_count_clean;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      <Metric
        label="Raw Rows"
        value={row_count_raw.toLocaleString()}
        accent="maroon"
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
        }
      />
      <Metric
        label="Clean Rows"
        value={row_count_clean.toLocaleString()}
        sub={rowsRemoved > 0 ? `−${rowsRemoved} removed` : 'No rows removed'}
        accent="success"
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
      />
      <Metric
        label="Columns"
        value={column_count}
        accent="purple"
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" />
          </svg>
        }
      />
      <Metric
        label="Duplicates"
        value={duplicate_count}
        accent={duplicate_count > 0 ? 'warning' : 'success'}
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        }
      />
      <Metric
        label="Outliers"
        value={total_outliers}
        accent={total_outliers > 0 ? 'danger' : 'success'}
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        }
      />
      <Metric
        label="Cols w/ Missing"
        value={missingCols}
        accent={missingCols > 0 ? 'warning' : 'success'}
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
        }
      />
    </div>
  );
}
