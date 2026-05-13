const STYLES = {
  green:   'bg-success/10 text-success border-success/25',
  success: 'bg-success/10 text-success border-success/25',
  red:     'bg-danger/10 text-red-400 border-danger/25',
  danger:  'bg-danger/10 text-red-400 border-danger/25',
  amber:   'bg-warning/10 text-warning border-warning/25',
  warning: 'bg-warning/10 text-warning border-warning/25',
  blue:    'bg-blue-500/10 text-blue-400 border-blue-500/25',
  slate:   'bg-white/[0.06] text-ink-secondary border-white/[0.12]',
  default: 'bg-white/[0.06] text-ink-secondary border-white/[0.12]',
  maroon:  'bg-maroon-600/15 text-maroon-400 border-maroon-600/30',
  purple:  'bg-purple-500/10 text-purple-400 border-purple-500/25',
  indigo:  'bg-indigo-500/10 text-indigo-400 border-indigo-500/25',
};

export default function Badge({ children, color = 'slate', className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${STYLES[color]} ${className}`}
    >
      {children}
    </span>
  );
}
