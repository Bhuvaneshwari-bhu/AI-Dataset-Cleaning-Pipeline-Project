export default function EmptyState({ icon, title, description, action, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center text-center py-14 px-6 ${className}`}>
      <div className="w-16 h-16 bg-white/[0.04] border border-white/[0.08] rounded-2xl flex items-center justify-center mb-5">
        {icon ?? (
          <svg className="w-7 h-7 text-ink-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        )}
      </div>
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      {description && <p className="text-sm text-ink-muted mt-2 max-w-xs leading-relaxed">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
