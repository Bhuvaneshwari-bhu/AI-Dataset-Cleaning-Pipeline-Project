export default function Card({ children, className = '', padding = true, hover = false }) {
  return (
    <div
      className={`
        bg-card border border-white/[0.08] rounded-2xl shadow-card
        transition-all duration-200
        ${hover ? 'hover:bg-card-hover hover:border-white/[0.14] hover:shadow-card-hover cursor-pointer' : ''}
        ${padding ? 'p-6' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-5">
      <div>
        <h3 className="text-sm font-semibold text-ink uppercase tracking-wider">{title}</h3>
        {subtitle && <p className="text-xs text-ink-muted mt-1">{subtitle}</p>}
      </div>
      {action && <div className="flex-shrink-0 ml-4">{action}</div>}
    </div>
  );
}
