import { useState } from 'react';
import Badge from '../ui/Badge';
import EmptyState from '../ui/EmptyState';

const PAGE_SIZE = 8;

function fmt(val, decimals = 2) {
  if (val === null || val === undefined) return <span className="text-slate-300">—</span>;
  return typeof val === 'number' ? val.toFixed(decimals) : val;
}

export default function ProfilesTable({ profiles = {} }) {
  const [page, setPage] = useState(0);
  const rows = Object.entries(profiles);
  const totalPages = Math.ceil(rows.length / PAGE_SIZE);
  const visible = rows.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  if (!rows.length) {
    return <EmptyState title="No profile data available" />;
  }

  return (
    <div>
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {['Column', 'Type', 'Nulls', 'Null %', 'Unique', 'Min', 'Max', 'Mean', 'Std'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {visible.map(([col, p]) => (
              <tr key={col} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-semibold text-slate-800 whitespace-nowrap">{col}</td>
                <td className="px-4 py-3">
                  <Badge color="slate">{p.dtype}</Badge>
                </td>
                <td className="px-4 py-3 text-slate-600">{p.null_count}</td>
                <td className="px-4 py-3">
                  <span className={p.null_pct > 20 ? 'text-red-600 font-semibold' : p.null_pct > 5 ? 'text-amber-600' : 'text-slate-500'}>
                    {p.null_pct.toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{p.unique_count}</td>
                <td className="px-4 py-3 text-slate-600 font-mono">{fmt(p.min_val)}</td>
                <td className="px-4 py-3 text-slate-600 font-mono">{fmt(p.max_val)}</td>
                <td className="px-4 py-3 text-slate-600 font-mono">{fmt(p.mean)}</td>
                <td className="px-4 py-3 text-slate-600 font-mono">{fmt(p.std)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3">
          <p className="text-xs text-slate-500">
            {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, rows.length)} of {rows.length} columns
          </p>
          <div className="flex gap-1">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              ← Prev
            </button>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
