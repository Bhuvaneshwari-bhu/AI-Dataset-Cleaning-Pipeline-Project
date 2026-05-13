import { useState, useRef, useCallback } from 'react';

const MAX_SIZE = 100 * 1024 * 1024; // 100 MB

function fmt(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function validate(file) {
  if (!file.name.toLowerCase().endsWith('.csv') && file.type !== 'text/csv') {
    return 'Only CSV files are supported.';
  }
  if (file.size === 0) return 'File is empty.';
  if (file.size > MAX_SIZE) return `File is too large (${fmt(file.size)}). Maximum is 100 MB.`;
  return null;
}

export default function DropZone({ onFileSelect, disabled = false }) {
  const [dragging, setDragging] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const handle = useCallback(
    (file) => {
      if (!file) return;
      const err = validate(file);
      if (err) {
        setError(err);
        setSelected(null);
        onFileSelect(null);
        return;
      }
      setError(null);
      setSelected(file);
      onFileSelect(file);
    },
    [onFileSelect],
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    handle(e.dataTransfer.files[0]);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    if (!disabled) setDragging(true);
  };

  const clear = (e) => {
    e.stopPropagation();
    setSelected(null);
    setError(null);
    onFileSelect(null);
  };

  const zoneClass = [
    'relative rounded-2xl p-12 text-center transition-all duration-200 select-none',
    disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer',
    dragging
      ? 'border-march scale-[1.01] bg-maroon-600/10'
      : selected
        ? 'border-2 border-dashed border-success/40 bg-success/5 cursor-default'
        : error
          ? 'border-2 border-dashed border-danger/40 bg-danger/5'
          : 'border-2 border-dashed border-white/[0.14] bg-card/50 hover:border-maroon-600/50 hover:bg-maroon-600/5',
  ].join(' ');

  return (
    <div
      className={zoneClass}
      onClick={() => !disabled && !selected && inputRef.current?.click()}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={() => setDragging(false)}
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => e.key === 'Enter' && !disabled && !selected && inputRef.current?.click()}
      aria-label="CSV file drop zone"
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={(e) => { handle(e.target.files[0]); e.target.value = ''; }}
        disabled={disabled}
      />

      {!selected ? (
        <div className="flex flex-col items-center gap-3">
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
            error
              ? 'bg-danger/10 border border-danger/20'
              : dragging
                ? 'bg-maroon-600/20 border border-maroon-600/30'
                : 'bg-white/[0.06] border border-white/[0.10]'
          }`}>
            <svg
              className={`w-8 h-8 ${error ? 'text-red-400' : dragging ? 'text-maroon-400' : 'text-ink-muted'}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              {error ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              )}
            </svg>
          </div>

          {error ? (
            <div>
              <p className="text-red-400 font-semibold">{error}</p>
              <p className="text-sm text-red-400/70 mt-1">Click to try a different file</p>
            </div>
          ) : (
            <div>
              <p className="text-ink font-semibold text-lg">
                {dragging ? 'Drop it here!' : 'Drag & drop your CSV file'}
              </p>
              <p className="text-ink-muted mt-1 text-sm">
                or <span className="text-maroon-400 font-semibold">click to browse</span>
              </p>
              <p className="text-ink-muted/60 text-xs mt-3">Supported: .csv · Max 100 MB</p>
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 min-w-0">
            <div className="w-12 h-12 bg-success/10 border border-success/20 rounded-xl flex items-center justify-center flex-shrink-0">
              <svg className="w-6 h-6 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-left min-w-0">
              <p className="font-semibold text-ink truncate">{selected.name}</p>
              <p className="text-sm text-ink-muted">{fmt(selected.size)}</p>
            </div>
          </div>
          {!disabled && (
            <button
              onClick={clear}
              className="flex-shrink-0 p-2 rounded-xl text-ink-muted hover:text-red-400 hover:bg-danger/10 transition-colors"
              aria-label="Remove file"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
