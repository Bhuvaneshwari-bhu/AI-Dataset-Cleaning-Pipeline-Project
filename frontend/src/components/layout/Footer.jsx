import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-base border-t border-white/[0.06] mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-maroon-gradient flex items-center justify-center">
              <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-ink-secondary">DataQuality Pipeline</span>
          </div>

          <nav className="flex items-center gap-5">
            <Link to="/" className="text-xs text-ink-muted hover:text-ink-secondary transition-colors">Home</Link>
            <Link to="/upload" className="text-xs text-ink-muted hover:text-ink-secondary transition-colors">Upload</Link>
          </nav>

          <p className="text-xs text-ink-muted">
            FastAPI · React · Pandas · Recharts
          </p>
        </div>
      </div>
    </footer>
  );
}
