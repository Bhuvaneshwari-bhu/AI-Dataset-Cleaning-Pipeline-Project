import { useState, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { getHealth } from '../../services/api';

function ApiStatus({ online }) {
  if (online === null) return null;
  return (
    <span className={`flex items-center gap-1.5 text-xs font-medium ${
      online ? 'text-success' : 'text-red-400'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${
        online ? 'bg-success animate-pulse' : 'bg-red-500'
      }`} />
      {online ? 'API Online' : 'API Offline'}
    </span>
  );
}

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [apiOnline, setApiOnline] = useState(null);
  const [scrolled, setScrolled] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    getHealth().then(() => setApiOnline(true)).catch(() => setApiOnline(false));
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const linkClass = ({ isActive }) =>
    `text-sm font-medium transition-colors duration-150 ${
      isActive ? 'text-maroon-400' : 'text-ink-muted hover:text-ink'
    }`;

  return (
    <header className={`sticky top-0 z-40 transition-all duration-300 ${
      scrolled
        ? 'bg-base/95 backdrop-blur-md border-b border-white/[0.08] shadow-[0_4px_24px_rgba(0,0,0,0.4)]'
        : 'bg-base/80 backdrop-blur-sm border-b border-white/[0.04]'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-maroon-gradient flex items-center justify-center flex-shrink-0 shadow-glow-maroon-sm group-hover:shadow-glow-maroon transition-shadow duration-200">
              <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <span className="font-bold text-ink text-[15px] tracking-tight">DataQuality</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-7">
            <NavLink to="/" end className={linkClass}>Home</NavLink>
            <NavLink to="/upload" className={linkClass}>Upload</NavLink>
            <div className="w-px h-4 bg-white/[0.12]" />
            <ApiStatus online={apiOnline} />
          </nav>

          {/* CTA + hamburger */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/upload')}
              className="hidden sm:inline-flex items-center gap-1.5 px-4 py-1.5 bg-maroon-gradient-r text-white text-sm font-semibold rounded-xl hover:brightness-110 hover:shadow-glow-maroon-sm transition-all duration-200"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Analyse
            </button>

            <button
              onClick={() => setMenuOpen(o => !o)}
              className="md:hidden p-2 text-ink-muted hover:text-ink rounded-lg hover:bg-white/[0.06] transition-colors"
              aria-label="Toggle menu"
            >
              {menuOpen ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-white/[0.06] py-3 pb-4 space-y-0.5 animate-slide-up">
            <NavLink to="/" end
              className={({ isActive }) =>
                `block px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive ? 'bg-maroon-600/15 text-maroon-400' : 'text-ink-secondary hover:text-ink hover:bg-white/[0.05]'
                }`
              }
              onClick={() => setMenuOpen(false)}
            >
              Home
            </NavLink>
            <NavLink to="/upload"
              className={({ isActive }) =>
                `block px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive ? 'bg-maroon-600/15 text-maroon-400' : 'text-ink-secondary hover:text-ink hover:bg-white/[0.05]'
                }`
              }
              onClick={() => setMenuOpen(false)}
            >
              Upload & Analyse
            </NavLink>
            <div className="px-3 py-2">
              <ApiStatus online={apiOnline} />
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
