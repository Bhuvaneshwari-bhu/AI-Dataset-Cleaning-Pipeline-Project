const SIZES = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-10 h-10',
  xl: 'w-14 h-14',
};

export default function Spinner({ size = 'md', className = '' }) {
  return (
    <svg
      className={`animate-spin text-maroon-500 ${SIZES[size]} ${className}`}
      fill="none"
      viewBox="0 0 24 24"
      aria-label="Loading"
    >
      <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-80" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
