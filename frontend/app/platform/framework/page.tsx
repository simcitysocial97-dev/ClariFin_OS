/**
 * Platform Framework Integrity Page — M9-C63 Phase E
 *
 * Surfaces C62 FrameworkIntegrityResult directly:
 * - Overall health (HEALTHY/DEGRADED/CRITICAL)
 * - Detector findings with classification and severity
 * - Self-test results (K1-K9)
 * - Artifact freshness summary
 * Data source: /platform/v1/framework/integrity, /platform/v1/framework/self-tests
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';
import { HealthBadge } from '@/components/platform/health-badge';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  FileText,
  RefreshCw,
  Shield,
  TestTube,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface DriftFinding {
  check_name: string;
  detected_component: string;
  expected_authority: string;
  actual_authority: string;
  classification: string;
  source_evidence: string;
  severity: string;
}

interface FrameworkIntegrityData {
  schema_version: string;
  generated_at: string;
  health: string;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  total_findings: number;
  findings: DriftFinding[];
  artifact_summary: Record<string, unknown>;
  diagnostic: {
    self_tests: Record<string, boolean>;
    passed: number;
    total: number;
  };
}

interface FrameworkIntegrityResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: FrameworkIntegrityData;
}

interface SelfTestResult {
  name: string;
  passed: boolean;
  detail: string | null;
}

interface SelfTestsData {
  results: SelfTestResult[];
  passed: number;
  total: number;
}

interface SelfTestsResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: SelfTestsData;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'text-red-400 bg-red-500/10 border-red-500/30',
  high: 'text-red-400 bg-red-500/10 border-red-500/30',
  medium: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  low: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  info: 'text-slate-400 bg-slate-500/10 border-slate-500/30',
};

const CLASSIFICATION_LABELS: Record<string, string> = {
  IMPLEMENTATION_DEFECT: 'Implementation Defect',
  AUTHORITY_DRIFT: 'Authority Drift',
  CONFIGURATION_DRIFT: 'Configuration Drift',
  CI_BYPASS: 'CI Bypass',
  EVIDENCE_INTEGRITY_DEFECT: 'Evidence Integrity Defect',
  ARTIFACT_INTEGRITY_DEFECT: 'Artifact Integrity Defect',
  FALSE_POSITIVE: 'False Positive',
  PRE_EXISTING: 'Pre-existing',
  ENVIRONMENTAL: 'Environmental',
  UNRELATED: 'Unrelated',
};

export default function FrameworkIntegrityPage() {
  const { data: integrityData, isLoading: integrityLoading, refetch: refetchIntegrity } = useQuery<FrameworkIntegrityResponse, Error>({
    queryKey: ['platform', 'framework', 'integrity'],
    queryFn: () => apiFetchJson('/platform/v1/framework/integrity') as Promise<FrameworkIntegrityResponse>,
    staleTime: 60_000,
  });

  const { data: selfTestsData, isLoading: selfTestsLoading } = useQuery<SelfTestsResponse, Error>({
    queryKey: ['platform', 'framework', 'self-tests'],
    queryFn: () => apiFetchJson('/platform/v1/framework/self-tests') as Promise<SelfTestsResponse>,
    staleTime: 60_000,
  });

  const d = integrityData?.data;
  const st = selfTestsData?.data;

  return (
    <div className="flex flex-col gap-4 max-w-5xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/platform" className="text-xs text-[var(--text-tertiary)] underline hover:text-[var(--text-secondary)]">
          ← Platform Console
        </Link>
        <div>
          <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Shield className="h-5 w-5 text-violet-400" />
            Framework Integrity
          </h1>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
            C62 self-diagnostic surface · authority drift + artifact freshness + K1-K9 self-tests
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => { refetchIntegrity(); }}
            disabled={integrityLoading}
            className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-default)] hover:bg-[var(--surface-raised)] transition-colors flex items-center gap-1"
          >
            <RefreshCw className={cn('h-3 w-3', integrityLoading && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      {integrityLoading && (
        <div className="text-sm text-[var(--text-tertiary)] py-8">Loading framework integrity…</div>
      )}

      {d && (
        <>
          {/* Overall Health Banner */}
          <OverallHealthBanner health={d.health} generatedAt={d.generated_at} />

          {/* Summary Counts */}
          <SummaryCounts
            critical={d.critical_count}
            high={d.high_count}
            medium={d.medium_count}
            low={d.low_count}
            info={d.info_count}
            total={d.total_findings}
          />

          {/* Self-Tests */}
          <SelfTestsPanel tests={st?.results ?? []} passed={st?.passed ?? 0} total={st?.total ?? 0} loading={selfTestsLoading} />

          {/* Detector Findings */}
          <DetectorFindingsPanel findings={d.findings} artifactSummary={d.artifact_summary} />

          {/* Footer */}
          <div className="text-xs text-[var(--text-tertiary)] border-t border-[var(--border-subtle)] pt-2">
            Source: runtime/foundation/verification/authority_drift_detector.py + artifact_freshness_detector + FrameworkSelfTests
          </div>
        </>
      )}
    </div>
  );
}

function OverallHealthBanner({ health, generatedAt }: { health: string; generatedAt: string }) {
  const healthColor =
    health === 'HEALTHY' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' :
    health === 'DEGRADED' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' :
    'text-red-400 bg-red-500/10 border-red-500/30';

  const healthIcon =
    health === 'HEALTHY' ? <CheckCircle2 className="h-8 w-8 shrink-0" /> :
    health === 'DEGRADED' ? <AlertTriangle className="h-8 w-8 shrink-0" /> :
    <AlertTriangle className="h-8 w-8 shrink-0" />;

  return (
    <div className={cn('rounded-lg border p-4 flex items-center gap-4', healthColor)}>
      {healthIcon}
      <div className="flex-1">
        <div className="text-xl font-bold font-mono">{health}</div>
        <div className="text-sm opacity-80">Framework Integrity Status</div>
      </div>
      <div className="text-xs text-[var(--text-tertiary)] font-mono shrink-0">
        {generatedAt.slice(0, 19).replace('T', ' ')}
      </div>
    </div>
  );
}

function SummaryCounts({
  critical,
  high,
  medium,
  low,
  info,
  total,
}: {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  total: number;
}) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <SummaryTile label="Total" value={total} accent={total > 0 ? 'warning' : 'positive'} />
      <SummaryTile label="Critical" value={critical} accent={critical > 0 ? 'negative' : 'positive'} />
      <SummaryTile label="High" value={high} accent={high > 0 ? 'negative' : 'positive'} />
      <SummaryTile label="Medium" value={medium} accent={medium > 0 ? 'warning' : 'positive'} />
      <SummaryTile label="Low" value={low} accent={low > 0 ? 'warning' : 'positive'} />
      <SummaryTile label="Info" value={info} accent={info > 0 ? 'warning' : 'positive'} />
    </div>
  );
}

function SummaryTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: 'positive' | 'warning' | 'negative';
}) {
  const color =
    accent === 'positive' ? 'text-emerald-400' :
    accent === 'warning' ? 'text-amber-400' : 'text-red-400';
  return (
    <div className={cn(
      'rounded-lg border p-3',
      accent === 'positive' ? 'border-emerald-500/20 bg-emerald-500/5' :
      accent === 'warning' ? 'border-amber-500/20 bg-amber-500/5' :
      'border-red-500/20 bg-red-500/5',
    )}>
      <div className={cn('text-2xl font-bold font-mono', color)}>{value}</div>
      <div className="text-xs text-[var(--text-tertiary)]">{label}</div>
    </div>
  );
}

function SelfTestsPanel({
  tests,
  passed,
  total,
  loading,
}: {
  tests: SelfTestResult[];
  passed: number;
  total: number;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4">
        <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)]">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Loading self-tests…
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
          <TestTube className="h-4 w-4 text-amber-400" />
          K1-K9 Self-Tests
        </div>
        <div className={cn(
          'text-sm font-mono px-2 py-1 rounded',
          passed === total && total > 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400',
        )}>
          {passed}/{total} passed
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {tests.map((test) => (
          <span
            key={test.name}
            className={cn(
              'text-xs font-mono px-2 py-1 rounded',
              test.passed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400',
            )}
          >
            {test.name}: {test.passed ? 'PASS' : 'FAIL'}
          </span>
        ))}
      </div>
    </div>
  );
}

function DetectorFindingsPanel({
  findings,
  artifactSummary,
}: {
  findings: DriftFinding[];
  artifactSummary: Record<string, unknown>;
}) {
  if (findings.length === 0) {
    return (
      <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
          <FileText className="h-4 w-4 text-emerald-400" />
          Detector Findings
        </div>
        <div className="text-sm text-emerald-400">No findings — all detectors clean</div>
      </div>
    );
  }

  // Group by classification
  const byClassification: Record<string, DriftFinding[]> = {};
  for (const f of findings) {
    (byClassification[f.classification] ??= []).push(f);
  }

  return (
    <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
        <FileText className="h-4 w-4 text-red-400" />
        Detector Findings ({findings.length})
      </div>
      <div className="flex flex-col gap-3">
        {Object.entries(byClassification).map(([classification, items]) => (
          <ClassificationGroup key={classification} classification={classification} items={items} />
        ))}
      </div>

      {Object.keys(artifactSummary).length > 0 && (
        <div className="border-t border-[var(--border-subtle)] pt-3 mt-3">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Artifact Summary</div>
          <pre className="text-xs font-mono text-[var(--text-tertiary)] bg-[var(--surface-raised)] p-2 rounded overflow-auto">
            {JSON.stringify(artifactSummary, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function ClassificationGroup({
  classification,
  items,
}: {
  classification: string;
  items: DriftFinding[];
}) {
  const label = CLASSIFICATION_LABELS[classification] ?? classification;

  return (
    <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] p-3">
      <div className="flex items-center gap-2 text-xs font-semibold mb-2">
        <span className="px-1.5 py-0.5 rounded bg-[var(--surface-base)] text-[var(--text-tertiary)] font-mono">
          {label}
        </span>
        <span className="text-[var(--text-tertiary)]">({items.length})</span>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((f) => (
          <FindingRow key={f.check_name} finding={f} />
        ))}
      </div>
    </div>
  );
}

function FindingRow({ finding }: { finding: DriftFinding }) {
  const severityColor = SEVERITY_COLORS[finding.severity] ?? SEVERITY_COLORS.info;

  return (
    <div className={cn('rounded border p-3 text-xs', severityColor)}>
      <div className="flex items-start gap-2">
        <span className="font-mono shrink-0 text-[var(--text-secondary)] w-36 truncate">
          {finding.check_name}
        </span>
        <div className="flex-1 min-w-0">
          <div className="font-medium">{finding.detected_component}</div>
          <div className="text-[var(--text-tertiary)] truncate">{finding.source_evidence}</div>
        </div>
      </div>
    </div>
  );
}