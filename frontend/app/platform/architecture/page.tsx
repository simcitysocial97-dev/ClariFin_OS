/**
 * Platform Architecture Page — M9-C57 Phase 9B
 *
 * Architecture Safety Center: authorities, boundaries, duplicates,
 * bypasses, deprecations, unmapped capabilities.
 * Data source: /platform/v1/architecture/*.
 */

'use client';

import { useState } from 'react';
import {
  useArchitectureAuthorities,
  useArchitectureBoundaries,
  useArchitectureDuplicates,
  useArchitectureBypasses,
  useArchitectureDeprecations,
  useArchitectureUnmapped,
} from '@/lib/hooks/use-platform-architecture';
import { HealthBadge } from '@/components/platform/health-badge';
import {
  Shield,
  GitBranch,
  Copy,
  ArrowRightCircle,
  Trash2,
  Map,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

type Tab = 'authorities' | 'boundaries' | 'duplicates' | 'bypasses' | 'deprecations' | 'unmapped';

export default function ArchitecturePage() {
  const [activeTab, setActiveTab] = useState<Tab>('authorities');

  const authoritiesQ = useArchitectureAuthorities();
  const boundariesQ = useArchitectureBoundaries();
  const duplicatesQ = useArchitectureDuplicates();
  const bypassesQ = useArchitectureBypasses();
  const deprecationsQ = useArchitectureDeprecations();
  const unmappedQ = useArchitectureUnmapped();

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'authorities', label: 'Authorities', icon: <Shield className="h-3 w-3" /> },
    { key: 'boundaries', label: 'Boundaries', icon: <GitBranch className="h-3 w-3" /> },
    { key: 'duplicates', label: 'Duplicates', icon: <Copy className="h-3 w-3" /> },
    { key: 'bypasses', label: 'Bypasses', icon: <ArrowRightCircle className="h-3 w-3" /> },
    { key: 'deprecations', label: 'Deprecations', icon: <Trash2 className="h-3 w-3" /> },
    { key: 'unmapped', label: 'Unmapped', icon: <Map className="h-3 w-3" /> },
  ];

  const findingsQ = activeTab === 'boundaries' ? boundariesQ :
                    activeTab === 'duplicates' ? duplicatesQ :
                    activeTab === 'bypasses' ? bypassesQ :
                    activeTab === 'deprecations' ? deprecationsQ :
                    activeTab === 'unmapped' ? unmappedQ : null;

  const findings = findingsQ?.data?.data?.items ?? [];

  return (
    <div className="flex flex-col gap-4 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Shield className="h-5 w-5 text-violet-400" />
          Architecture Safety Center
        </h1>
        <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
          Exposes live C50 authority state: configuration, route, capability, decision, efficiency
        </p>
      </div>

      {/* Summary bar */}
      <SummaryBar authorities={authoritiesQ.data?.data?.items ?? []} />

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[var(--border-subtle)] flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === tab.key
                ? 'border-violet-400 text-violet-400'
                : 'border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]',
            )}
          >
            {tab.icon}
            {tab.label}
            {tab.key !== 'authorities' && findingsQ && (
              <span className="ml-1 text-xs opacity-60">{findingsQ.data?.data?.count ?? 0}</span>
            )}
          </button>
        ))}
      </div>

      {/* Authorities view */}
      {activeTab === 'authorities' && <AuthoritiesPanel authorities={authoritiesQ.data?.data?.items ?? []} loading={authoritiesQ.isLoading} />}

      {/* Findings views */}
      {activeTab !== 'authorities' && (
        <FindingsPanel
          items={findings}
          loading={findingsQ?.isLoading ?? false}
          emptyLabel={
            activeTab === 'boundaries' ? 'No boundary violations'
            : activeTab === 'duplicates' ? 'No duplicate authorities'
            : activeTab === 'bypasses' ? 'No bypass attempts detected'
            : activeTab === 'deprecations' ? 'No deprecated patterns found'
            : 'All capabilities mapped'
          }
        />
      )}

      {/* Footer */}
      <div className="text-xs text-[var(--text-tertiary)] border-t border-[var(--border-subtle)] pt-2">
        Source: runtime/foundation/verification/{'configuration_authority.py, route_authority.py, capability_authority.py, control_plane_efficiency.py'}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function SummaryBar({
  authorities,
}: {
  authorities: { name: string; status: string; issues: number }[];
}) {
  const healthy = authorities.filter((a) => a.status === 'HEALTHY').length;
  const unhealthy = authorities.filter((a) => a.status === 'UNHEALTHY').length;
  const degraded = authorities.filter((a) => a.status === 'DEGRAD').length;
  const totalIssues = authorities.reduce((s, a) => s + a.issues, 0);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <SummaryTile label="Healthy" value={healthy} accent="positive" />
      <SummaryTile label="Degraded" value={degraded} accent="warning" />
      <SummaryTile label="Unhealthy" value={unhealthy} accent="negative" />
      <SummaryTile label="Total Issues" value={totalIssues} accent={totalIssues > 0 ? 'negative' : 'positive'} />
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

// ---------------------------------------------------------------------------

function AuthoritiesPanel({
  authorities,
  loading,
}: {
  authorities: { name: string; owner: string; status: string; last_check: string; issues: number }[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)] py-8">
        <RefreshCw className="h-4 w-4 animate-spin" />
        Loading authorities…
      </div>
    );
  }

  if (authorities.length === 0) {
    return (
      <div className="py-8 text-sm text-[var(--text-tertiary)] text-center">No authorities registered</div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {authorities.map((a) => (
        <div
          key={a.name}
          className="flex items-center gap-4 px-4 py-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] hover:border-[var(--border-default)] transition-colors"
        >
          <HealthBadge status={a.status} size="sm" />
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-[var(--text-primary)]">{a.name}</div>
            <div className="text-xs font-mono text-[var(--text-tertiary)] truncate">{a.owner}</div>
          </div>
          <div className="text-right shrink-0">
            <div className={cn(
              'text-sm font-mono',
              a.issues > 0 ? 'text-red-400' : 'text-emerald-400',
            )}>
              {a.issues} issue{a.issues !== 1 ? 's' : ''}
            </div>
            <div className="text-xs text-[var(--text-tertiary)] font-mono">{a.last_check}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------

function FindingsPanel({
  items,
  loading,
  emptyLabel,
}: {
  items: { id: string; severity: string; title: string; location: string; evidence: string[]; first_seen?: string | null }[];
  loading: boolean;
  emptyLabel: string;
}) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)] py-8">
        <RefreshCw className="h-4 w-4 animate-spin" />
        Loading findings…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-12 text-[var(--text-tertiary)]">
        <Shield className="h-8 w-8 opacity-40" />
        <span className="text-sm">{emptyLabel}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((issue) => (
        <FindingCard key={issue.id} issue={issue} />
      ))}
    </div>
  );
}

function FindingCard({
  issue,
}: {
  issue: { id: string; severity: string; title: string; location: string; evidence: string[] };
}) {
  const severityColor =
    issue.severity === 'high' ? 'text-red-400 border-red-500/30 bg-red-500/5' :
    issue.severity === 'medium' ? 'text-amber-400 border-amber-500/30 bg-amber-500/5' :
    'text-blue-400 border-blue-500/30 bg-blue-500/5';

  return (
    <div className={cn('flex items-start gap-3 px-4 py-3 rounded-lg border', severityColor)}>
      <span className="text-xs font-mono shrink-0 w-16">{issue.severity.toUpperCase()}</span>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold">{issue.title}</div>
        <div className="text-xs font-mono text-[var(--text-tertiary)] mt-0.5">{issue.location}</div>
        {issue.evidence.length > 0 && (
          <div className="text-xs font-mono text-[var(--text-tertiary)] mt-1 truncate">
            evidence: {issue.evidence.join(', ')}
          </div>
        )}
      </div>
      <span className="font-mono text-xs text-[var(--text-tertiary)] shrink-0">{issue.id}</span>
    </div>
  );
}
