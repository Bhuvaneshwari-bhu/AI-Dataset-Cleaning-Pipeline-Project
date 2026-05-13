import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-6">
      <div className="text-center max-w-md">
        <p className="text-8xl font-extrabold text-maroon-600/20 select-none">404</p>
        <h1 className="text-2xl font-bold text-ink mt-2">Page not found</h1>
        <p className="text-ink-muted mt-3">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4">
          <Link
            to="/"
            className="px-6 py-2.5 bg-maroon-gradient-r text-white font-semibold rounded-xl hover:brightness-110 hover:shadow-glow-maroon-sm transition-all duration-200"
          >
            Go Home
          </Link>
          <Link
            to="/upload"
            className="px-6 py-2.5 bg-white/[0.06] border border-white/[0.12] text-ink-secondary font-semibold rounded-xl hover:bg-white/[0.10] hover:text-ink transition-all duration-200"
          >
            Upload Dataset
          </Link>
        </div>
      </div>
    </div>
  );
}
