/**
 * Platform Diagnostic Center — M9-C63 Phase G
 *
 * Consolidated diagnostic surface per C63 §10.
 * Categories:
 *   - FAILED: task → capability → source → test/evidence
 *   - BLOCKED: reason → timeout/dependency/environment/obligation → partial evidence
 *   - INTERRUPTED: signal → run state → recovery status
 *   - STALE: artifact → identity mismatch/age/generator mismatch
 *   - DIVERGED: authority/configuration/registry mismatch → specific detector
 *
 * Data flows: UI → Platform API → canonical control plane → canonical executor
 * No second diagnosis engine — surfaces C50/C62 authoritative state.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  XCircle,
  PauseCircle,
  Clock,
  GitBranch,
  ChevronDown,
  ChevronUp,
  Filter,
  Bug,
  FileText,
  Activity,
  ShieldCheck,
  Zap,
  Info,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useConsolidatedDiagnostics } from '@/lib/hooks/use-platform-diagnostics';
import { usePlatformHealth } from '@/lib/hooks/use-platform-health';
import { usePlatformEvents } from '@/lib/hooks/use-platform-events';
import { useDiagnose } from '@/lib/hooks/use-platform-diagnostics';

type Category = 'FAILED' | 'BLOCKED' | 'INTERRUPTED' | 'STALE' | 'DIVERGED';

const CATEGORY_CONFIG: Record<Category, {
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
  description: string;
}> = {
  FAILED: {
    icon: XCircle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    description: 'Verification executed but failed — defect detected with evidence chain',
  },
  BLOCKED: {
    icon: AlertCircle,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    description: 'Execution cannot proceed — infrastructure, timeout, validation, or authorization',
  },
  INTERRUPTED: {
    icon: PauseCircle,
    color: 'text-gray-400',
    bgColor: 'bg-gray-500/10',
    borderColor: 'border-gray-500/30',
    description: 'Operator terminated — SIGINT/SIGTERM with run state and recovery status',
  },
  STALE: {
    icon: Clock,
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/30',
    description: 'Artifact exceeds freshness threshold or has identity/generator mismatch',
  },
  DIVERGED: {
    icon: GitBranch,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    description: 'Authority/configuration/registry mismatch — specific detector provenance',
  },
};

const CATEGORY_ORDER: Category[] = ['FAILED', 'BLOCKED', 'INTERRUPTED', 'STALE', 'DIVERGED'];

export default function DiagnosticCenterPage() {
  const { categories } = useConsolidatedDiagnostics();
  const { data: health } = usePlatformHealth();
  const { data: eventsData } = usePlatformEvents(10);
  const diagnoseMutation = useDiagnose();

  const [expandedCategories, setExpandedCategories] = useState<Set<Category>>(
    new Set(CATEGORY_ORDER.filter(c => categories.some(cat => cat.category === c)))
  );
  const [activeSymptom, setActiveSymptom] = useState('');

  const totalItems = categories.reduce((sum, cat) => sum + cat.items.length, 0);

  const handleDiagnose = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSymptom.trim()) return;
    await diagnoseMutation.mutateAsync({
      symptom: activeSymptom,
      error_code: undefined,
      capability_id: undefined,
    });
    setActiveSymptom('');
  };

  const toggleCategory = (category: Category) => {
    const newSet = new Set(expandedCategories);
    if (newSet.has(category)) newSet.delete(category);
    else newSet.add(category);
    setExpandedCategories(newSet);
  };

  const isExpanded = (category: Category) => expandedCategories.has(category);

  return (
    <div className="flex flex-col gap-4 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
              <Bug className="h-5 w-5 text-red-400" />
              Diagnostic Center
            </h1>
            <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
              Consolidated deterministic diagnostics — C63 §10 · 5 categories · {totalItems} finding(s)
            </p>
          </div>
          <div className="flex items-center gap-2">
            <SystemHealthBadge health={health?.data} />
          </div>
        </div>

        {/* Quick diagnose form */}
        <form onSubmit={handleDiagnose} className="flex gap-2">
          <input
            type="text"
            value={activeSymptom}
            onChange={(e) => setActiveSymptom(e.target.value)}
            placeholder="Enter symptom for deterministic diagnosis (L0-L5)..."
            className="flex-1 px-3 py-2 text-sm bg-[var(--surface-base)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:border-violet-500/50 focus:outline-none"
            disabled={diagnoseMutation.isPending}
          />
          <button
            type="submit"
            disabled={!activeSymptom.trim() || diagnoseMutation.isPending}
            className="px-4 py-2 text-sm font-medium bg-violet-500/20 text-violet-300 border border-violet-500/30 rounded-lg hover:bg-violet-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {diagnoseMutation.isPending ? 'Diagnosing...' : 'Diagnose'}
          </button>
        </form>

        {/* Diagnostic result */}
        {diagnoseMutation.data && (
          <DiagnosticResultPanel result={diagnoseMutation.data} onClose={() => diagnoseMutation.reset()} />
        )}
      </div>

      {/* Diagnostic Categories */}
      <div className="flex flex-col gap-3">
        {categories.length === 0 ? (
          <EmptyState />
        ) : (
          categories.map((cat) => (
            <DiagnosticCategoryPanel
              key={cat.category}
              category={cat}
              config={CATEGORY_CONFIG[cat.category]}
              isExpanded={isExpanded(cat.category)}
              onToggle={() => toggleCategory(cat.category)}
            />
          ))
        )}
      </div>

      {/* Quick Actions / Related Pages */}
      <RelatedActions events={eventsData?.data?.items} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function SystemHealthBadge({ health }: { health?: any }) {
  if (!health) return null;
  const platform = health.platform ?? 'UNKNOWN';
  const framework = health.framework_integrity ?? 'UNKNOWN';

  const getColor = (status: string) => {
    if (status === 'HEALTHY') return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (status === 'DEGRAD' || status === 'DEGRADED') return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    if (status === 'UNHEALTHY' || status === 'CRITICAL') return 'text-red-400 border-red-500/30 bg-red-500/10';
    return 'text-gray-400 border-gray-500/30 bg-gray-500/10';
  };

  return (
    <div className="flex items-center gap-2">
      <span className={cn('text-xs font-bold font-mono px-2 py-0.5 rounded border', getColor(platform))}>
        {platform}
      </span>
      <span className="text-xs text-[var(--text-tertiary)]">·</span>
      <span className={cn('text-xs font-bold font-mono px-2 py-0.5 rounded border', getColor(framework))}>
        Framework: {framework}
      </span>
    </div>
  );
}

function DiagnosticResultPanel({
  result,
  onClose,
}: {
  result: any;
  onClose: () => void;
}) {
  const data = result.data;
  const levelColors: Record<string, string> = {
    L0: 'text-emerald-400',
    L1: 'text-blue-400',
    L2: 'text-violet-400',
    L3: 'text-amber-400',
    L4: 'text-orange-400',
    L5: 'text-red-400',
  };

  return (
    <div className="rounded-lg border border-violet-500/30 bg-violet-500/5 p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={cn('text-sm font-bold font-mono px-2 py-0.5 rounded', levelColors[data.level] ?? 'text-gray-400')}>
            {data.level}
          </span>
          <span className="text-sm font-semibold text-[var(--text-primary)]">Diagnostic Result</span>
        </div>
        <button onClick={onClose} className="text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]">✕</button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div>
          <span className="text-[var(--text-tertiary)]">Symptom:</span>
          <span className="ml-2 font-mono text-[var(--text-primary)]">{data.symptom}</span>
        </div>
        <div>
          <span className="text-[var(--text-tertiary)]">Fact:</span>
          <span className="ml-2 font-mono text-[var(--text-primary)]">{data.fact}</span>
        </div>
        {data.error_code && (
          <div>
            <span className="text-[var(--text-tertiary)]">Error Code:</span>
            <span className="ml-2 font-mono text-[var(--text-primary)]">{data.error_code}</span>
          </div>
        )}
        {data.capability_id && (
          <div>
            <span className="text-[var(--text-tertiary)]">Capability:</span>
            <span className="ml-2 font-mono text-[var(--text-primary)]">{data.capability_id}</span>
          </div>
        )}
        {data.affected_capability && (
          <div>
            <span className="text-[var(--text-tertiary)]">Affected:</span>
            <span className="ml-2 font-mono text-[var(--text-primary)]">{data.affected_capability}</span>
          </div>
        )}
        <div className="sm:col-span-2">
          <span className="text-[var(--text-tertiary)]">Evidence:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {data.evidence.map((e: string, i: number) => (
              <span key={i} className="font-mono text-[var(--text-secondary)] px-2 py-0.5 bg-[var(--surface-base)] rounded border border-[var(--border-subtle)]">{e}</span>
            ))}
          </div>
        </div>
        <div className="sm:col-span-2">
          <span className="text-[var(--text-tertiary)]">Recommendation:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {data.recommendation.map((r: any, i: number) => (
              <span key={i} className="font-mono text-[var(--text-primary)] px-2 py-0.5 bg-violet-500/10 rounded border border-violet-500/30">
                {r.action} → {r.target}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-center border border-[var(--border-subtle)] rounded-lg">
      <AlertTriangle className="h-12 w-12 text-[var(--text-tertiary)] opacity-40" />
      <div className="text-sm text-[var(--text-secondary)]">No diagnostic findings</div>
      <div className="text-xs text-[var(--text-tertiary)] max-w-md">
        All monitored systems report healthy. Run a verification or enter a symptom above
        to trigger deterministic diagnostic reasoning (L0-L5 ladder).
      </div>
    </div>
  );
}

function DiagnosticCategoryPanel({
  category,
  config,
  isExpanded,
  onToggle,
}: {
  category: { category: Category; items: any[] };
  config: typeof CATEGORY_CONFIG[keyof typeof CATEGORY_CONFIG];
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const Icon = config.icon;
  const items = category.items;

  return (
    <div className={cn('rounded-lg border overflow-hidden', config.borderColor)}>
      {/* Category Header */}
      <button
        onClick={onToggle}
        className={cn(
          'w-full flex items-center gap-3 px-4 py-3 transition-colors',
          config.bgColor
        )}
      >
        <Icon className={cn('h-5 w-5 shrink-0', config.color)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-[var(--text-primary)]">{category.category}</span>
            <span className={cn('text-xs font-mono px-2 py-0.5 rounded', config.borderColor.replace('border-', 'bg-'))}>
              {items.length}
            </span>
          </div>
          <div className="text-xs text-[var(--text-tertiary)] mt-0.5">{config.description}</div>
        </div>
        <span className={cn(
          'text-[var(--text-tertiary)] transition-transform',
          isExpanded ? 'rotate-180' : ''
        )}>
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </span>
      </button>

      {/* Category Items */}
      {isExpanded && (
        <div className="border-t border-[var(--border-subtle)] p-4">
          <div className="flex flex-col gap-3">
            {items.map((item) => (
              <DiagnosticItemCard key={item.id} item={item} categoryColor={config.color} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DiagnosticItemCard({
  item,
  categoryColor,
}: {
  item: any;
  categoryColor: string;
}) {
  return (
    <div className="border border-[var(--border-subtle)] rounded-lg p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-[var(--text-primary)]">{item.title}</span>
            <span className={cn('text-xs font-mono px-1.5 py-0.5 rounded', categoryColor.replace('text-', 'bg-').replace('400', '500/20'), categoryColor.replace('text-', 'text-'))}>
              {item.provenance.status}
            </span>
          </div>
          <div className="text-xs text-[var(--text-tertiary)] mt-1 font-mono">{item.id}</div>
        </div>
        <Link
          href={`/platform/diagnostics/detail/${encodeURIComponent(item.id)}`}
          className="text-xs px-2 py-1 rounded bg-[var(--surface-raised)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-interactive)] transition-colors shrink-0"
        >
          Detail
        </Link>
      </div>

      {/* Metadata */}
      <div className="flex flex-wrap gap-3 text-xs">
        <span className="flex items-center gap-1 text-[var(--text-secondary)]">
          <FileText className="h-3 w-3" />
          <span className="font-mono">{item.capability}</span>
        </span>
        <span className="flex items-center gap-1 text-[var(--text-tertiary)]">
          <Activity className="h-3 w-3" />
          <span className="font-mono">{item.source}</span>
        </span>
        <span className="flex items-center gap-1 text-[var(--text-tertiary)]">
          <ShieldCheck className="h-3 w-3" />
          <span className="font-mono">{item.provenance.decision}</span>
        </span>
      </div>

      {/* Detail */}
      <div className="text-xs text-[var(--text-secondary)] font-mono">{item.detail}</div>

      {/* Provenance */}
      <div className="border-t border-[var(--border-subtle)] pt-3 flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-1 text-[var(--text-tertiary)]">
          <Info className="h-3 w-3" />
          <span>Detector: <span className="font-mono text-[var(--text-secondary)]">{item.provenance.detector}</span></span>
        </div>
        <div className="flex items-center gap-1 text-[var(--text-tertiary)]">
          <Activity className="h-3 w-3" />
          <span>Time: <span className="font-mono text-[var(--text-secondary)]">{item.provenance.timestamp.slice(11, 19)}</span></span>
        </div>
        {item.provenance.run_id && (
          <div className="flex items-center gap-1 text-[var(--text-tertiary)]">
            <FileText className="h-3 w-3" />
            <span>Run: <span className="font-mono text-[var(--text-secondary)]">{item.provenance.run_id.slice(0, 12)}...</span></span>
          </div>
        )}
        <div className="flex items-center gap-1 text-[var(--text-tertiary)]">
          <Filter className="h-3 w-3" />
          <span>Reason: <span className="font-mono text-[var(--text-secondary)]">{item.provenance.diagnostic_reason}</span></span>
        </div>
      </div>

      {/* Evidence */}
      {item.evidence.length > 0 && (
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[var(--text-tertiary)]">Evidence:</span>
          <div className="flex flex-wrap gap-1">
            {item.evidence.map((e: string, i: number) => (
              <span key={i} className="font-mono text-[var(--text-secondary)] px-2 py-0.5 bg-[var(--surface-base)] rounded border border-[var(--border-subtle)]">{e}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RelatedActions({
  events,
}: {
  events?: any[];
}) {
  return (
    <div className="rounded-lg border border-[var(--border-subtle)] p-4 flex flex-col gap-3">
      <div className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
        <Zap className="h-4 w-4 text-violet-400" />
        Quick Actions
      </div>
      <div className="flex flex-wrap gap-2">
        <Link
          href="/platform/verification"
          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-violet-500/50 hover:bg-violet-500/10 transition-colors flex items-center gap-1"
        >
          <Activity className="h-3 w-3" />
          Run Verification
        </Link>
        <Link
          href="/platform/diagnostics/change"
          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-blue-500/50 hover:bg-blue-500/10 transition-colors flex items-center gap-1"
        >
          <Zap className="h-3 w-3" />
          Change Intelligence
        </Link>
        <Link
          href="/platform/errors"
          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-red-500/50 hover:bg-red-500/10 transition-colors flex items-center gap-1"
        >
          <AlertTriangle className="h-3 w-3" />
          Error Observatory
        </Link>
        <Link
          href="/platform/framework"
          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-emerald-500/50 hover:bg-emerald-500/10 transition-colors flex items-center gap-1"
        >
          <ShieldCheck className="h-3 w-3" />
          Framework Integrity
        </Link>
        <Link
          href="/platform/architecture"
          className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] hover:border-purple-500/50 hover:bg-purple-500/10 transition-colors flex items-center gap-1"
        >
          <GitBranch className="h-3 w-3" />
          Architecture Safety
        </Link>
      </div>

      {events && events.length > 0 && (
        <div className="border-t border-[var(--border-subtle)] pt-3">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Recent Events</div>
          <div className="flex flex-col gap-1">
            {events.slice(0, 3).map((ev) => (
              <div key={ev.id} className="flex items-center gap-2 text-xs font-mono text-[var(--text-tertiary)]">
                <span className="w-20 shrink-0">{ev.emitted_at?.slice(11, 19)}</span>
                <span className="text-[var(--text-secondary)]">{ev.event_type}</span>
                <span className="truncate">{ev.task_id ?? ev.execution_id ?? ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}