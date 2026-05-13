import { Link } from 'react-router-dom';

const FEATURES = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'bg-success/10 text-success',
    title: 'Smart Validation',
    desc: 'Schema enforcement, type checking, range violations, and format pattern matching across all columns.',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    ),
    color: 'bg-maroon-600/15 text-maroon-400',
    title: 'Auto Cleaning',
    desc: 'Intelligent missing value imputation (median, mean, mode), duplicate removal, and whitespace normalisation.',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    color: 'bg-purple-500/10 text-purple-400',
    title: 'Anomaly Detection',
    desc: 'IQR and Z-score methods detect outliers in every numeric column, with configurable sensitivity thresholds.',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    color: 'bg-warning/10 text-warning',
    title: 'Quality Reports',
    desc: 'Scored HTML reports with column profiles, distribution charts, and a full audit trail of all transformations.',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    color: 'bg-blue-500/10 text-blue-400',
    title: 'Clean Export',
    desc: 'Download the fully cleaned and transformed dataset as CSV, ready for modelling or downstream pipelines.',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    color: 'bg-maroon-600/15 text-maroon-300',
    title: 'REST API',
    desc: 'Every pipeline action is exposed as a typed FastAPI endpoint with OpenAPI docs and full validation.',
  },
];

const STEPS = [
  { n: '01', title: 'Upload CSV', desc: 'Drag and drop or browse to select your dataset file.' },
  { n: '02', title: 'Configure', desc: 'Choose anomaly method, fill strategy, and threshold.' },
  { n: '03', title: 'Analyse', desc: 'The pipeline validates, cleans, and scores your data.' },
  { n: '04', title: 'Download', desc: 'Export the cleaned file and open the full quality report.' },
];

const TECH = ['FastAPI', 'React', 'Pandas', 'Recharts', 'Tailwind CSS', 'Scikit-learn'];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-base">
      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-base">
        {/* Background radial glow */}
        <div className="absolute inset-0 bg-hero-glow pointer-events-none" />
        {/* Blob accents */}
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-maroon-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-maroon-800/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-28 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-maroon-600/15 border border-maroon-600/30 text-maroon-300 text-sm font-medium mb-8">
            <span className="w-2 h-2 rounded-full bg-maroon-400 animate-pulse" />
            AI-powered data quality pipeline
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-tight tracking-tight mb-6 text-ink">
            Clean Data,{' '}
            <span className="bg-maroon-gradient bg-clip-text text-transparent">
              Confident Models
            </span>
          </h1>

          <p className="text-xl text-ink-muted max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload a CSV and get a quality score, automated cleaning, outlier detection, and a
            full HTML report — in seconds.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/upload"
              className="px-8 py-4 bg-maroon-gradient-r text-white font-bold text-lg rounded-2xl hover:brightness-110 hover:shadow-glow-maroon hover:-translate-y-0.5 transition-all duration-200 shadow-glow-maroon-sm"
            >
              Analyse Your Dataset →
            </Link>
            <a
              href="#how-it-works"
              className="px-8 py-4 bg-white/[0.06] hover:bg-white/[0.10] text-ink-secondary font-semibold text-lg rounded-2xl border border-white/[0.12] hover:border-white/[0.20] transition-all duration-200"
            >
              How it works
            </a>
          </div>

          {/* Stats row */}
          <div className="mt-20 grid grid-cols-2 sm:grid-cols-4 gap-px bg-white/[0.06] rounded-2xl overflow-hidden max-w-3xl mx-auto border border-white/[0.08]">
            {[
              { v: '100%', l: 'Real pipeline' },
              { v: 'IQR + Z', l: 'Outlier methods' },
              { v: '6-stage', l: 'Pipeline' },
              { v: '< 30s', l: 'Avg. analysis' },
            ].map(({ v, l }) => (
              <div key={l} className="bg-card/60 px-6 py-5">
                <p className="text-2xl font-extrabold text-ink">{v}</p>
                <p className="text-xs text-ink-muted mt-1">{l}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────── */}
      <section className="py-24 bg-card/30 border-t border-white/[0.04]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-ink">Everything your data needs</h2>
            <p className="text-ink-muted mt-3 text-lg max-w-xl mx-auto">
              A complete quality pipeline, not just a linter.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="bg-card border border-white/[0.08] rounded-2xl shadow-card p-6 hover:border-white/[0.14] hover:shadow-glow-maroon-sm hover:-translate-y-0.5 transition-all duration-200"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${f.color}`}>
                  {f.icon}
                </div>
                <h3 className="font-bold text-ink text-lg mb-2">{f.title}</h3>
                <p className="text-ink-muted text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────── */}
      <section id="how-it-works" className="py-24 bg-base border-t border-white/[0.04]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-ink">From upload to insight in 4 steps</h2>
          </div>

          <div className="relative">
            <div className="hidden lg:block absolute top-10 left-1/2 -translate-x-1/2 w-3/4 h-px bg-white/[0.06]" />

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              {STEPS.map((s) => (
                <div key={s.n} className="relative flex flex-col items-center text-center">
                  <div className="w-20 h-20 rounded-2xl bg-maroon-gradient flex flex-col items-center justify-center shadow-glow-maroon-sm mb-5 z-10">
                    <span className="text-xs font-bold text-maroon-200">{s.n}</span>
                    <span className="text-white font-bold text-base leading-tight mt-0.5 px-2">{s.title}</span>
                  </div>
                  <p className="text-ink-muted text-sm leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Tech Stack ───────────────────────────────────── */}
      <section className="py-16 bg-card/30 border-t border-white/[0.04]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-xs font-semibold text-ink-muted uppercase tracking-widest mb-6">Built with</p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {TECH.map((t) => (
              <span
                key={t}
                className="px-4 py-2 bg-card border border-white/[0.08] rounded-xl text-sm font-semibold text-ink-secondary hover:border-maroon-600/40 hover:text-ink transition-colors duration-150"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────── */}
      <section className="py-24 bg-maroon-gradient border-t border-maroon-600/40">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4 text-white">Ready to clean your data?</h2>
          <p className="text-maroon-200 text-lg mb-10">
            Upload a CSV and get a full quality report in under 30 seconds.
          </p>
          <Link
            to="/upload"
            className="inline-flex items-center gap-3 px-10 py-4 bg-white text-maroon-700 font-bold text-lg rounded-2xl hover:bg-maroon-50 transition-all shadow-xl hover:-translate-y-0.5"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Upload Your Dataset
          </Link>
        </div>
      </section>
    </div>
  );
}
