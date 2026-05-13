import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DropZone from '../components/upload/DropZone';
import ProgressBar, { IndeterminateBar } from '../components/ui/ProgressBar';
import Spinner from '../components/ui/Spinner';
import { useUpload } from '../hooks/useUpload';
import { useAnalysis } from '../hooks/useAnalysis';
import { useToast } from '../hooks/useToast';

const STATUS = { IDLE: 'idle', UPLOADING: 'uploading', ANALYZING: 'analyzing', ERROR: 'error' };

const SELECT_CLS =
  'w-full border border-white/[0.12] rounded-xl px-3 py-2.5 text-sm text-ink-secondary bg-card-elevated focus:ring-2 focus:ring-maroon-500/50 focus:border-maroon-500/50 transition-shadow outline-none';

export default function UploadPage() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { upload, uploading, uploadProgress } = useUpload();
  const { analyze } = useAnalysis();

  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(STATUS.IDLE);
  const [errorMsg, setErrorMsg] = useState('');
  const [options, setOptions] = useState({
    anomaly_method: 'iqr',
    fill_strategy: 'median',
    anomaly_threshold: 1.5,
  });

  const canSubmit = !!file && (status === STATUS.IDLE || status === STATUS.ERROR);

  const set = (key) => (e) => {
    const val = key === 'anomaly_threshold' ? parseFloat(e.target.value) : e.target.value;
    setOptions((o) => ({ ...o, [key]: val }));
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setErrorMsg('');

    try {
      setStatus(STATUS.UPLOADING);
      const uploaded = await upload(file);

      setStatus(STATUS.ANALYZING);
      const result = await analyze(uploaded.upload_id, options);

      sessionStorage.setItem(`analysis_${uploaded.upload_id}`, JSON.stringify(result));

      addToast('Analysis complete!', 'success');
      navigate(`/dashboard/${uploaded.upload_id}`, { state: { result } });
    } catch (err) {
      setStatus(STATUS.ERROR);
      setErrorMsg(err.message);
      addToast(err.message, 'error');
    }
  };

  const busy = status === STATUS.UPLOADING || status === STATUS.ANALYZING;

  return (
    <div className="max-w-2xl mx-auto px-4 py-14">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-3xl font-extrabold text-ink">Upload Dataset</h1>
        <p className="text-ink-muted mt-2">
          Select a CSV file and configure the pipeline options, then click <strong className="text-ink-secondary">Analyse</strong>.
        </p>
      </div>

      {/* Drop zone */}
      <DropZone onFileSelect={setFile} disabled={busy} />

      {/* Options */}
      {!busy && (
        <div className="mt-6 bg-card border border-white/[0.08] rounded-2xl shadow-card p-6">
          <h2 className="text-sm font-semibold text-ink-secondary mb-4 uppercase tracking-wide">Pipeline Options</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-ink-muted mb-1.5 uppercase tracking-wide">
                Anomaly Method
              </label>
              <select
                value={options.anomaly_method}
                onChange={set('anomaly_method')}
                className={SELECT_CLS}
                style={{ colorScheme: 'dark' }}
              >
                <option value="iqr">IQR</option>
                <option value="zscore">Z-Score</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink-muted mb-1.5 uppercase tracking-wide">
                Fill Strategy
              </label>
              <select
                value={options.fill_strategy}
                onChange={set('fill_strategy')}
                className={SELECT_CLS}
                style={{ colorScheme: 'dark' }}
              >
                <option value="median">Median</option>
                <option value="mean">Mean</option>
                <option value="mode">Mode</option>
                <option value="drop">Drop Row</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink-muted mb-1.5 uppercase tracking-wide">
                Threshold
              </label>
              <input
                type="number"
                value={options.anomaly_threshold}
                onChange={set('anomaly_threshold')}
                step="0.1"
                min="0.1"
                max="10"
                className={SELECT_CLS}
                style={{ colorScheme: 'dark' }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Upload progress */}
      {status === STATUS.UPLOADING && (
        <div className="mt-6 bg-card border border-white/[0.08] rounded-2xl p-5 shadow-card animate-fade-in">
          <div className="flex justify-between text-sm font-medium text-ink-secondary mb-2">
            <span>Uploading file…</span>
            <span className="text-maroon-400">{uploadProgress}%</span>
          </div>
          <ProgressBar value={uploadProgress} />
        </div>
      )}

      {/* Analyzing */}
      {status === STATUS.ANALYZING && (
        <div className="mt-6 bg-card border border-maroon-600/20 rounded-2xl p-8 shadow-card text-center animate-fade-in">
          <Spinner size="lg" className="mx-auto" />
          <p className="mt-4 font-semibold text-ink">Analysing dataset…</p>
          <p className="text-sm text-ink-muted mt-1">Validation · Cleaning · Anomaly detection · Report generation</p>
          <IndeterminateBar className="mt-5 max-w-xs mx-auto" />
        </div>
      )}

      {/* Error */}
      {status === STATUS.ERROR && errorMsg && (
        <div className="mt-4 flex items-start gap-3 p-4 bg-danger/10 border border-danger/20 rounded-xl animate-fade-in">
          <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          <p className="text-sm text-red-400">{errorMsg}</p>
        </div>
      )}

      {/* Submit */}
      {!busy && (
        <button
          onClick={handleAnalyze}
          disabled={!canSubmit}
          className="mt-6 w-full py-3.5 bg-maroon-gradient-r disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-base rounded-2xl transition-all shadow-glow-maroon-sm/50 hover:brightness-110 hover:shadow-glow-maroon hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-maroon-500/50 focus:ring-offset-2 focus:ring-offset-base"
        >
          {status === STATUS.ERROR ? 'Retry Analysis' : 'Analyse Dataset →'}
        </button>
      )}

      {/* Hint */}
      {status === STATUS.IDLE && !file && (
        <p className="text-center text-xs text-ink-muted mt-4">Select a file to enable analysis</p>
      )}
    </div>
  );
}
