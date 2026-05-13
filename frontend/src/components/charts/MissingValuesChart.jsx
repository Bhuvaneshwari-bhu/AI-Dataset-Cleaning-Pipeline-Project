import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import EmptyState from '../ui/EmptyState';

const MAROON_PALETTE = ['#A63A50', '#C0507D', '#D4789A', '#E8A0B8', '#7B1E3A', '#CB6088', '#B84870', '#9B2F5A'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-card-elevated border border-white/[0.12] rounded-xl shadow-card px-4 py-3 text-sm">
      <p className="font-semibold text-ink">{label}</p>
      <p className="text-maroon-400 mt-1">
        {payload[0].value} missing ({payload[0].payload.pct?.toFixed(1)}%)
      </p>
    </div>
  );
};

export default function MissingValuesChart({ missingSummary = {} }) {
  const data = Object.entries(missingSummary)
    .map(([col, info]) => ({ col, count: info.count, pct: info.pct }))
    .sort((a, b) => b.count - a.count);

  if (!data.length) {
    return (
      <EmptyState
        title="No missing values"
        description="All columns have complete data."
        className="py-10"
      />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="col"
          tick={{ fontSize: 12, fill: '#6B6B78' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#6B6B78' }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={MAROON_PALETTE[i % MAROON_PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
