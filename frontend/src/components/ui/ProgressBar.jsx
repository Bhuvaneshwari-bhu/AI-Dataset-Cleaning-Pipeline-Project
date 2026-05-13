const FILLS = {
  maroon:  'bg-maroon-gradient-r',
  success: 'bg-success',
  warning: 'bg-warning',
  danger:  'bg-danger',
  muted:   'bg-white/20',
};

export default function ProgressBar({ value = 0, max = 100, color = 'maroon', showLabel = false, className = '' }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className={`w-full ${className}`}>
      <div className="w-full bg-white/[0.08] rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${FILLS[color]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <p className="text-xs text-ink-muted mt-1 text-right tabular-nums">{pct.toFixed(0)}%</p>
      )}
    </div>
  );
}

export function IndeterminateBar({ className = '' }) {
  return (
    <div className={`w-full bg-white/[0.06] rounded-full h-0.5 overflow-hidden ${className}`}>
      <div
        className="h-full w-1/3 bg-maroon-gradient-r rounded-full"
        style={{ animation: 'indeterminate 1.6s ease-in-out infinite' }}
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
