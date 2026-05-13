import { getReportUrl, getDownloadUrl } from '../../services/api';

export default function ReportActions({ uploadId }) {
  const reportUrl = getReportUrl(uploadId);
  const downloadUrl = getDownloadUrl(uploadId);

  return (
    <div className="flex flex-wrap gap-3">
      <a
        href={reportUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-5 py-2.5 bg-maroon-gradient-r text-white text-sm font-semibold rounded-xl hover:brightness-110 hover:shadow-glow-maroon-sm transition-all duration-200 shadow-glow-maroon-sm/50"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Open Full Report
      </a>

      <a
        href={downloadUrl}
        download
        className="inline-flex items-center gap-2 px-5 py-2.5 bg-success/10 text-success border border-success/25 text-sm font-semibold rounded-xl hover:bg-success/20 transition-all duration-200"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Download Cleaned CSV
      </a>

      <a
        href="/upload"
        className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/[0.06] text-ink-secondary border border-white/[0.12] text-sm font-semibold rounded-xl hover:bg-white/[0.10] hover:text-ink transition-all duration-200"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Analyze Another Dataset
      </a>
    </div>
  );
}
