/**
 * Platform Workflows Page — M9-C67.2
 *
 * Canonical workflow inventory from /platform/v1/workflows.
 * Same source as `verify inspect workflows`.
 *
 * Differentiates LOCAL vs GITHUB_ONLY vs ENVIRONMENT_BOUNDARY vs
 * EXTERNAL_TOOLING vs EXTERNAL_SERVICE vs BROWSER without implying
 * non-local workflows are broken.
 */

'use client';

import { useState, useMemo } from 'react';
import { usePlatformWorkflows, getBoundaryColor, getBoundaryDescription } from '@/lib/hooks/use-platform-workflows';
import type { WorkflowItem } from '@/lib/hooks/use-platform-workflows';
import { HealthBadge } from '@/components/platform/health-badge';
import {
  Terminal,
  Search,
  Filter,
  GitBranch,
  Cloud,
  Monitor,
  Cpu,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const BOUNDARY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  LOCAL: Monitor,
  GITHUB_ONLY: GitBranch,
  ENVIRONMENT_BOUNDARY: Cpu,
  EXTERNAL_TOOLING: Terminal,
  EXTERNAL_SERVICE: Cloud,
  BROWSER: Monitor,
};

export default function PlatformWorkflowsPage() {
  const { data, isLoading, error } = usePlatformWorkflows();
  const [search, setSearch] = useState('');
  const [boundaryFilter, setBoundaryFilter] = useState<string>('all');

  const items = useMemo(() => data?.data?.items ?? [], [data?.data?.items]);
  const totalCount = data?.data?.count ?? 0;

  const filtered = useMemo(() => {
    let result = items;
    if (boundaryFilter !== 'all') {
      result = result.filter((w) => w.boundary_classification === boundaryFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (w) =>
          w.name.toLowerCase().includes(q) ||
          w.workflow_id.toLowerCase().includes(q) ||
          w.path.toLowerCase().includes(q) ||
          w.canonical_command.toLowerCase().includes(q),
      );
    }
    return result;
  }, [items, boundaryFilter, search]);

  const boundaries = useMemo(() => {
    const set = new Set(items.map((w) => w.boundary_classification));
    return Array.from(set).sort();
  }, [items]);

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return <ApiErrorState message={error.message} />;
  }

  return (
    <div className="flex flex-col gap-4 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Terminal className="h-5 w-5 text-violet-400" />
            Workflows
          </h1>
          <p className="text-sm text-[var(--text-tertiary)] mt-0.5">
            {totalCount} workflows · canonical source: runtime.foundation.verification.workflow_inspection
          </p>
        </div>
        <div className="text-xs font-mono text-[var(--text-tertiary)]">
          {data?.data?.source ?? ''}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-tertiary)]" />
          <input
            type="text"
            placeholder="Search workflows..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--border-default)]"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-[var(--text-tertiary)]" />
          <select
            value={boundaryFilter}
            onChange={(e) => setBoundaryFilter(e.target.value)}
            className="text-sm rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] text-[var(--text-primary)] px-3 py-1.5 focus:outline-none focus:border-[var(--border-default)]"
          >
            <option value="all">All boundaries</option>
            {boundaries.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>
        <span className="text-xs text-[var(--text-tertiary)] font-mono">
          {filtered.length} of {totalCount}
        </span>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs">
        {boundaries.map((b) => {
          const Icon = BOUNDARY_ICONS[b] ?? GitBranch;
          return (
            <span key={b} className="flex items-center gap-1 text-[var(--text-tertiary)]">
              <Icon className={cn('h-3 w-3', getBoundaryColor(b))} />
              {b}
              <span className="text-[var(--text-tertiary)/60]">
                ({filtered.filter((w) => w.boundary_classification === b).length})
              </span>
            </span>
          );
        })}
      </div>

      {/* Workflow list */}
      {filtered.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex flex-col gap-2">
          {filtered.map((workflow) => (
            <WorkflowCard key={workflow.workflow_id} workflow={workflow} />
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="border-t border-[var(--border-subtle)] pt-3 text-xs text-[var(--text-tertiary)] font-mono">
        UI → Platform API → workflow_inspection.enumerate_workflows() → no second executor
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function WorkflowCard({ workflow }: { workflow: WorkflowItem }) {
  const BoundaryIcon = BOUNDARY_ICONS[workflow.boundary_classification] ?? GitBranch;

  return (
    <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4 hover:border-[var(--border-default)] transition-colors">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-[var(--text-primary)]">{workflow.name}</span>
            <span className={cn(
              'text-xs font-mono px-2 py-0.5 rounded border',
              getBoundaryColor(workflow.boundary_classification),
            )}>
              <BoundaryIcon className="h-3 w-3 inline mr-1" />
              {workflow.boundary_classification}
            </span>
            {workflow.local_executable ? (
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Local OK
              </span>
            ) : (
              <span className="text-xs px-2 py-0.5 rounded bg-slate-500/10 text-slate-400 border border-slate-500/30">
                Non-local
              </span>
            )}
          </div>
          <div className="text-xs font-mono text-[var(--text-tertiary)] mt-0.5 truncate">
            {workflow.path}
          </div>
        </div>
      </div>

      <div className="text-xs text-[var(--text-tertiary)] mb-2">
        {getBoundaryDescription(workflow.boundary_classification)}
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        {workflow.commands.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="text-[var(--text-tertiary)]">Commands:</span>
            <code className="font-mono text-violet-300">{workflow.canonical_command}</code>
          </div>
        )}
        {workflow.triggers.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="text-[var(--text-tertiary)]">Triggers:</span>
            <span className="font-mono text-[var(--text-secondary)]">{workflow.triggers.join(', ')}</span>
          </div>
        )}
        {workflow.parity_status && (
          <div className="flex items-center gap-1">
            <span className="text-[var(--text-tertiary)]">Parity:</span>
            <HealthBadge status={workflow.parity_status} size="sm" showLabel />
          </div>
        )}
      </div>

      {workflow.environment_requirements.length > 0 && (
        <div className="mt-2 text-[10px] text-[var(--text-tertiary)] font-mono">
          Requires: {workflow.environment_requirements.join(', ')}
        </div>
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="flex items-center gap-2 text-sm text-[var(--text-tertiary)]">
        <Terminal className="h-4 w-4 animate-pulse" />
        Loading workflows...
      </div>
    </div>
  );
}

function ApiErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center border border-red-500/30 rounded-lg bg-red-500/5">
      <div className="text-red-400 text-lg font-semibold">API UNAVAILABLE</div>
      <div className="text-sm text-[var(--text-secondary)] max-w-md">{message}</div>
      <div className="text-xs text-[var(--text-tertiary)] font-mono">
        Unable to retrieve workflow inventory from the backend.
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-2 py-16 text-[var(--text-tertiary)]">
      <Terminal className="h-8 w-8 opacity-40" />
      <span className="text-sm">No workflows match your filters</span>
      <span className="text-xs">Try adjusting search or boundary filter</span>
    </div>
  );
}
