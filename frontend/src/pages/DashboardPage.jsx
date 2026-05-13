import { useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import Card, { CardHeader } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import QualityGauge from '../components/charts/QualityGauge';
import MissingValuesChart from '../components/charts/MissingValuesChart';
import OutlierChart from '../components/charts/OutlierChart';
import OverviewCards from '../components/dashboard/OverviewCards';
import ProfilesTable from '../components/dashboard/ProfilesTable';
import MissingSummary from '../components/dashboard/MissingSummary';
import CleaningLog from '../components/dashboard/CleaningLog';
import ReportActions from '../components/dashboard/ReportActions';

function SectionHeading({ children }) {
  return <h2 className="text-lg font-bold text-ink mb-4">{children}</h2>;
}

function ViolationList({ items, emptyText }) {
  if (!items || !items.length) {
    return <p className="text-sm text-success font-medium">✓ {emptyText}</p>;
  }
  return (
    <ul className="space-y-1.5">
      {items.map((v, i) => (
        <li key={i} className="text-sm text-ink-secondary flex items-start gap-2">
          <span className="text-maroon-400 flex-shrink-0 mt-0.5">•</span>
          <span>{v}</span>
        </li>
      ))}
    </ul>
  );
}

function SchemaViolations({ schemaViolations = {} }) {
  const entries = Object.entries(schemaViolations);
  if (!entries.length) return <p className="text-sm text-success font-medium">✓ No schema violations</p>;
  return (
    <ul className="space-y-2">
      {entries.map(([col, msgs]) => (
        <li key={col}>
          <p className="text-sm font-semibold text-ink">{col}</p>
          {msgs.map((m, i) => (
            <p key={i} className="text-sm text-red-400 ml-3">• {m}</p>
          ))}
        </li>
      ))}
    </ul>
  );
}

function FormatViolations({ formatViolations = {} }) {
  const entries = Object.entries(formatViolations);
  if (!entries.length) return <p className="text-sm text-success font-medium">✓ No format violations</p>;
  return (
    <ul className="space-y-3">
      {entries.map(([col, info]) => (
        <li key={col} className="text-sm">
          <p className="font-semibold text-ink">{col}</p>
          <p className="text-ink-muted ml-3">
            Pattern: <code className="text-xs bg-white/[0.06] border border-white/[0.08] px-1.5 py-0.5 rounded font-mono">{info.pattern}</code>
          </p>
          <p className="text-red-400 ml-3">{info.invalid_count} invalid — samples: {info.sample_values?.slice(0, 3).join(', ')}</p>
        </li>
      ))}
    </ul>
  );
}

export default function DashboardPage() {
  const { uploadId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [result] = useState(() => {
    if (location.state?.result) return location.state.result;
    try {
      const stored = sessionStorage.getItem(`analysis_${uploadId}`);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  if (!result) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-24">
        <EmptyState
          title="No analysis data found"
          description="Analysis data is not available for this ID. This can happen after a page refresh. Please upload and analyse a new dataset."
          action={
            <Button onClick={() => navigate('/upload')}>
              Upload a Dataset
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 animate-fade-in">

      {/* ── Page header ───────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-ink">Analysis Results</h1>
          <p className="text-sm text-ink-muted mt-1 font-mono">ID: {uploadId}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge color={result.passed ? 'success' : 'danger'} className="text-sm px-3 py-1.5">
            {result.passed ? '✓ Quality Check Passed' : '✗ Quality Check Failed'}
          </Badge>
        </div>
      </div>

      {/* ── Quality gauge + overview cards ────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-[auto_1fr] gap-6 items-start">
        <Card className="flex flex-col items-center py-8 px-10">
          <p className="text-xs font-semibold text-ink-muted mb-5 uppercase tracking-widest">Quality Score</p>
          <QualityGauge score={result.quality_score} passed={result.passed} />
        </Card>
        <OverviewCards result={result} />
      </div>

      {/* ── Charts ────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Missing Values by Column" subtitle="Columns with null / NaN entries" />
          <MissingValuesChart missingSummary={result.missing_summary} />
        </Card>
        <Card>
          <CardHeader
            title="Outliers by Column"
            subtitle={`${result.total_outliers} total outliers detected`}
          />
          <OutlierChart outlierSummary={result.outlier_summary} />
        </Card>
      </div>

      {/* ── Column Profiles ───────────────────────────── */}
      <Card>
        <CardHeader
          title="Column Profiles"
          subtitle={`Descriptive statistics for all ${result.column_count} columns`}
        />
        <ProfilesTable profiles={result.profiles} />
      </Card>

      {/* ── Missing values detail + Cleaning log ──────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Data Quality Details" subtitle="Missing values and type issues" />
          <MissingSummary missingSummary={result.missing_summary} typeIssues={result.type_issues} />
        </Card>
        <Card>
          <CardHeader title="Cleaning Log" subtitle={`${result.clean_log?.length || 0} transformation(s) applied`} />
          <CleaningLog cleanLog={result.clean_log} />
        </Card>
      </div>

      {/* ── Violations ────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader title="Schema Violations" />
          <SchemaViolations schemaViolations={result.schema_violations} />
        </Card>
        <Card>
          <CardHeader title="Format Violations" />
          <FormatViolations formatViolations={result.format_violations} />
        </Card>
        <Card>
          <CardHeader title="Type Issues" />
          <ViolationList items={result.type_issues} emptyText="No type issues" />
        </Card>
      </div>

      {/* ── Report Actions ────────────────────────────── */}
      <Card>
        <CardHeader title="Export & Reports" subtitle="Open the full HTML report or download the cleaned dataset" />
        <ReportActions uploadId={uploadId} />
      </Card>
    </div>
  );
}
