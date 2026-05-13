import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div className="min-h-screen bg-base flex items-center justify-center p-6">
        <div className="bg-card border border-white/[0.08] rounded-2xl shadow-card p-10 max-w-md w-full text-center animate-scale-in">
          <div className="w-14 h-14 bg-danger/10 border border-danger/20 rounded-full flex items-center justify-center mx-auto mb-5">
            <svg className="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-ink mb-2">Something went wrong</h2>
          <p className="text-sm text-ink-muted mb-7">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            onClick={() => window.location.replace('/')}
            className="px-6 py-2.5 bg-maroon-gradient-r text-white font-semibold rounded-xl transition-all hover:brightness-110"
          >
            Return to Home
          </button>
        </div>
      </div>
    );
  }
}
