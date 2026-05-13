export default function ProgressBar({ value = 0, max = 100, color = 'indigo', showLabel = false, className = '' }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  const TRACK_COLORS = {
    indigo: 'bg-indigo-600',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
  };

  return (
    <div className={`w-full ${className}`}>
      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${TRACK_COLORS[color]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <p className="text-xs text-slate-500 mt-1 text-right">{pct.toFixed(0)}%</p>
      )}
    </div>
  );
}

/** Indeterminate animated bar for unknown durations */
export function IndeterminateBar({ className = '' }) {
  return (
    <div className={`w-full bg-slate-200 rounded-full h-1.5 overflow-hidden ${className}`}>
      <div className="h-full w-1/3 bg-indigo-600 rounded-full animate-[slide_1.5s_ease-in-out_infinite]"
        style={{ animation: 'indeterminate 1.5s ease-in-out infinite' }}
      />
      <style>{`
        @keyframes indeterminate {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(400%); }
        }
      `}</style>
    </div>
  );
}
