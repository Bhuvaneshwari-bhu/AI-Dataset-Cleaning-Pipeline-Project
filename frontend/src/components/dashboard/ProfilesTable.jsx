import { useState } from 'react';
import Badge from '../ui/Badge';
import EmptyState from '../ui/EmptyState';

const PAGE_SIZE = 8;

function fmt(val, decimals = 2) {
  if (val === null || val === undefined) return <span className="text-ink-muted/40">—</span>;
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
      <div className="overflow-x-auto rounded-xl border border-white/[0.08]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-card-elevated border-b border-white/[0.08]">
              {['Column', 'Type', 'Nulls', 'Null %', 'Unique', 'Min', 'Max', 'Mean', 'Std'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-ink-muted uppercase tracking-wide whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {visible.map(([col, p]) => (
              <tr key={col} className="even:bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                <td className="px-4 py-3 font-semibold text-ink whitespace-nowrap">{col}</td>
                <td className="px-4 py-3">
                  <Badge color="default">{p.dtype}</Badge>
                </td>
                <td className="px-4 py-3 text-ink-secondary">{p.null_count}</td>
                <td className="px-4 py-3">
                  <span className={
                    p.null_pct > 20
                      ? 'text-red-400 font-semibold'
                      : p.null_pct > 5
                        ? 'text-warning font-medium'
                        : 'text-ink-muted'
                  }>
                    {p.null_pct.toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-ink-secondary">{p.unique_count}</td>
                <td className="px-4 py-3 text-ink-secondary font-mono text-xs">{fmt(p.min_val)}</td>
                <td className="px-4 py-3 text-ink-secondary font-mono text-xs">{fmt(p.max_val)}</td>
                <td className="px-4 py-3 text-ink-secondary font-mono text-xs">{fmt(p.mean)}</td>
                <td className="px-4 py-3 text-ink-secondary font-mono text-xs">{fmt(p.std)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3">
          <p className="text-xs text-ink-muted">
            {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, rows.length)} of {rows.length} columns
          </p>
          <div className="flex gap-1">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-white/[0.10] text-ink-secondary bg-white/[0.04] hover:bg-white/[0.08] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              ← Prev
            </button>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-white/[0.10] text-ink-secondary bg-white/[0.04] hover:bg-white/[0.08] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
