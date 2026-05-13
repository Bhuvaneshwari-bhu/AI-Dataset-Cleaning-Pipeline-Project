import { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);
let _id = 0;

const CONFIG = {
  success: {
    bar: 'bg-success',
    icon: (
      <svg className="w-4 h-4 text-success flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  error: {
    bar: 'bg-danger',
    icon: (
      <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  warning: {
    bar: 'bg-warning',
    icon: (
      <svg className="w-4 h-4 text-warning flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  info: {
    bar: 'bg-maroon-500',
    icon: (
      <svg className="w-4 h-4 text-maroon-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
};

function ToastItem({ toast, onRemove }) {
  const cfg = CONFIG[toast.type] ?? CONFIG.info;
  return (
    <div className="relative bg-card-elevated border border-white/[0.10] rounded-2xl shadow-card w-80 overflow-hidden animate-slide-in-right">
      {/* Colour accent bar */}
      <div className={`absolute left-0 top-0 bottom-0 w-0.5 ${cfg.bar} rounded-l-2xl`} />
      <div className="flex items-start gap-3 px-4 py-3 pl-5">
        {cfg.icon}
        <p className="text-sm text-ink-secondary font-medium flex-1 leading-snug">{toast.message}</p>
        <button
          onClick={() => onRemove(toast.id)}
          className="flex-shrink-0 text-ink-muted hover:text-ink transition-colors mt-0.5"
          aria-label="Dismiss"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function ToastContainer({ toasts, onRemove }) {
  if (!toasts.length) return null;
  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2" role="region" aria-label="Notifications">
      {toasts.map(t => <ToastItem key={t.id} toast={t} onRemove={onRemove} />)}
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4500) => {
    const id = ++_id;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
  }, []);

  const removeToast = useCallback(id => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}
