const VARIANTS = {
  primary:
    'bg-maroon-gradient-r text-white shadow-glow-maroon-sm ' +
    'hover:shadow-glow-maroon hover:brightness-110 ' +
    'active:brightness-90',
  secondary:
    'bg-white/[0.06] text-ink-secondary border border-white/[0.12] ' +
    'hover:bg-white/[0.10] hover:border-white/[0.20] hover:text-ink',
  danger:
    'bg-danger text-white hover:bg-red-700 shadow-sm',
  ghost:
    'text-ink-muted hover:text-ink hover:bg-white/[0.06]',
  success:
    'bg-success text-white hover:brightness-110 shadow-glow-success',
  outline:
    'border border-maroon-600/50 text-maroon-400 hover:bg-maroon-600/10 hover:border-maroon-500/70',
};

const SIZES = {
  sm: 'px-3 py-1.5 text-xs rounded-lg',
  md: 'px-4 py-2 text-sm rounded-xl',
  lg: 'px-6 py-2.5 text-sm rounded-xl',
  xl: 'px-8 py-3.5 text-base rounded-2xl',
};

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  className = '',
  onClick,
  type = 'button',
  ...props
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center gap-2 font-semibold
        transition-all duration-200 focus-visible:ring-2 focus-visible:ring-maroon-500/50
        disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none
        ${VARIANTS[variant]} ${SIZES[size]} ${className}
      `}
      {...props}
    >
      {loading && (
        <svg className="animate-spin w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}
