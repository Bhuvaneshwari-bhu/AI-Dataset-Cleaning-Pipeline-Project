import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import EmptyState from '../ui/EmptyState';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg px-4 py-3 text-sm">
      <p className="font-semibold text-slate-800">{label}</p>
      <p className="text-orange-600 mt-1">
        {payload[0].value} outliers ({payload[0].payload.pct?.toFixed(2)}%)
      </p>
    </div>
  );
};

export default function OutlierChart({ outlierSummary = {} }) {
  const data = Object.entries(outlierSummary)
    .filter(([, info]) => info.count > 0)
    .map(([col, info]) => ({ col, count: info.count, pct: info.pct }))
    .sort((a, b) => b.count - a.count);

  if (!data.length) {
    return (
      <EmptyState
        title="No outliers detected"
        description="All numeric columns are within normal bounds."
        className="py-10"
      />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="col"
          tick={{ fontSize: 12, fill: '#64748b' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#64748b' }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#fff7ed' }} />
        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={`hsl(${25 + i * 8}, 85%, ${55 + i * 2}%)`} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
