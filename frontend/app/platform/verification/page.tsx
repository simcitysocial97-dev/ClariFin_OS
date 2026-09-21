/**
 * Verification Center — M9-C63 Phase F
 *
 * Canonical command vocabulary:
 *   check, plan, run, diagnose, strengthen, inspect, certify, ci, doctor
 *
 * Roadmap requirements:
 *   capability, profile/operation, status, last run, duration, evidence, action
 * Detail: owner, stage, command, dependencies, recent executions,
 *         evidence, cache status, health, failure history
 * Actions: Run capability, Run group, Run affected, Run full, Cancel,
 *          Inspect evidence
 *
 * Every run enters the C50 task/execution path (via /verification/run*).
 * The execution stream is SSE at /executions/{id}/stream.
 */

'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useCapabilities, useRecentVerificationRuns, useVerificationRun, useVerificationRunAffected, useVerificationRunFull, useVerificationRunGroup, useVerificationRecommendation } from '@/lib/hooks/use-verification-center';
import { HealthBadge } from '@/components/platform/health-badge';
import {
  Play,
  Zap,
  Stethoscope,
  Shield,
  Search,
  CheckCircle2,
  Terminal,
  RotateCcw,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Canonical command vocabulary per C63 spec
const CANONICAL_COMMANDS = [
  { id: 'check', label: 'Check', icon: CheckCircle2, description: 'Quick validation of changed capabilities', color: 'text-emerald-400' },
  { id: 'plan', label: 'Plan', icon: Search, description: 'Compute blast radius & obligation set', color: 'text-blue-400' },
  { id: 'run', label: 'Run', icon: Play, description: 'Execute verification for capability/group', color: 'text-violet-400' },
  { id: 'diagnose', label: 'Diagnose', icon: Stethoscope, description: 'Deterministic failure analysis', color: 'text-amber-400' },
  { id: 'strengthen', label: 'Strengthen', icon: Shield, description: 'Mutation testing / test amplification', color: 'text-red-400' },
  { id: 'inspect', label: 'Inspect', icon: Zap, description: 'Evidence & artifact deep-dive', color: 'text-cyan-400' },
  { id: 'certify', label: 'Certify', icon: CheckCircle2, description: 'Full certification campaign', color: 'text-emerald-400' },
  { id: 'ci', label: 'CI', icon: RotateCcw, description: 'CI pipeline integration', color: 'text-blue-400' },
  { id: 'doctor', label: 'Doctor', icon: AlertTriangle, description: 'Environment & framework health', color: 'text-red-400' },
];

const COMPAT_ALIASES = [
  { alias: 'quick', canonical: 'run', note: 'legacy profile' },
  { alias: 'backend', canonical: 'run --group backend', note: 'legacy profile' },
  { alias: 'frontend', canonical: 'run --group frontend', note: 'legacy profile' },
  { alias: 'api-contracts', canonical: 'check', note: 'legacy profile' },
  { alias: 'runtime', canonical: 'doctor', note: 'legacy profile' },
  { alias: 'golden', canonical: 'inspect', note: 'legacy profile' },
  { alias: 'playwright', canonical: 'run --group e2e', note: 'legacy profile' },
];

export default function VerificationCenterPage() {
  const caps = useCapabilities();
  const recent = useRecentVerificationRuns(20);
  const recommendation = useVerificationRecommendation();
  const runOne = useVerificationRun();
  const runGroup = useVerificationRunGroup();
  const runAffected = useVerificationRunAffected();
  const runFull = useVerificationRunFull();

  const [filterStage, setFilterStage] = useState<string>('all');
  const [runResult, setRunResult] = useState<string | null>(null);
  const [showCommands, setShowCommands] = useState(false);

  const categories = caps.data?.data?.categories ?? [];
  const filtered = useMemo(() => {
    const items = caps.data?.data?.items ?? [];
    if (filterStage === 'all') return items;
    return items.filter((it) => String(it.stage).toLowerCase() === filterStage.toLowerCase());
  }, [caps.data, filterStage]);

  const mutate = async (kind: 'run' | 'group' | 'affected' | 'full', payload?: unknown) => {
    try {
      const res =
        kind === 'run'
          ? await runOne.mutateAsync({ capability_id: (payload as { capability_id?: string })?.capability_id ?? null })
          : kind === 'group'
            ? await runGroup.mutateAsync({ group: (payload as { group?: string })?.group ?? null })
            : kind === 'affected'
              ? await runAffected.mutateAsync()
              : await runFull.mutateAsync();
      setRunResult(`${res.kind} — ${res.data.message}`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setRunResult(`error: ${msg}`);
    }
  };

  return (
    <div className="flex flex-col gap-4 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Verification Center</h1>
          <p className="text-sm text-[var(--text-tertiary)]">Capabilities · Profiles · Evidence · Runs · Canonical Commands</p>
        </div>
        <div className="flex gap-2">
          <button
            className="px-3 py-1 rounded border border-[var(--border-subtle)] text-xs bg-[var(--surface-raised)]"
            onClick={() => void mutate('affected')}
          >
            <Zap className="h-3 w-3 mr-1" /> Run affected
          </button>
          <button
            className="px-3 py-1 rounded border border-[var(--border-subtle)] text-xs bg-[var(--surface-raised)]"
            onClick={() => void mutate('full')}
          >
            <RotateCcw className="h-3 w-3 mr-1" /> Run full
          </button>
          <button
            className="px-3 py-1 rounded border border-[var(--border-subtle)] text-xs bg-[var(--surface-raised)]"
            onClick={() => setShowCommands(!showCommands)}
          >
            <Terminal className="h-3 w-3 mr-1" /> Commands
          </button>
        </div>
      </div>

      {runResult && <div className="text-xs font-mono text-[var(--text-secondary)] border border-[var(--border-subtle)] p-2 rounded">{runResult}</div>}

      {/* Canonical Command Vocabulary */}
      {showCommands && (
        <CommandVocabularyPanel />
      )}

      {/* Verification Recommendation */}
      {recommendation.data && (
        <RecommendationPanel recommendation={recommendation.data.data} />
      )}

      {/* Filter by Stage */}
      <div className="flex gap-2 text-xs flex-wrap">
        <button className={cn('px-2 py-1 rounded', filterStage === 'all' ? 'bg-[var(--surface-raised)]' : '')} onClick={() => setFilterStage('all')}>
          All ({caps.data?.data?.count ?? 0})
        </button>
        {categories.map((c) => (
          <button
            key={c}
            className={cn('px-2 py-1 rounded', filterStage === c ? 'bg-[var(--surface-raised)]' : '')}
            onClick={() => setFilterStage(c)}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Capabilities Table */}
      <div className="rounded border border-[var(--border-subtle)] overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-[var(--surface-raised)] text-[var(--text-tertiary)]">
            <tr>
              <th className="text-left p-2">Capability</th>
              <th className="text-left p-2">Stage</th>
              <th className="text-left p-2">Cost</th>
              <th className="text-left p-2">Auth</th>
              <th className="text-left p-2">Last Run</th>
              <th className="text-left p-2">Duration</th>
              <th className="text-left p-2">Evidence</th>
              <th className="text-left p-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {caps.isLoading ? (
              <tr>
                <td className="p-2 text-[var(--text-tertiary)]" colSpan={8}>Loading…</td>
              </tr>
            ) : (
              filtered.map((it) => (
                <CapabilityRow key={it.id} cap={it} onRun={() => void mutate('run', { capability_id: it.id })} recentRuns={recent.data?.data?.items ?? []} />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Recent Runs */}
      {recent.data && (
        <div className="rounded border border-[var(--border-subtle)] p-3">
          <div className="text-xs font-semibold text-[var(--text-primary)] mb-2">Recent Runs</div>
          <div className="text-xs text-[var(--text-secondary)]">
            Showing {recent.data.data.items.length} of {recent.data.data.count}
          </div>
          <ul className="text-xs font-mono">
            {recent.data.data.items.slice(0, 10).map((r) => (
              <li key={r.id} className="flex items-center gap-2">
                <HealthBadge status={r.status} size="sm" showLabel={false} />
                <span>{r.id}</span>
                <span className="text-[var(--text-tertiary)]">{String(r.status)}</span>
                <span className="text-[var(--text-tertiary)]">{r.started_at}</span>
                {r.duration_ms && <span className="text-[var(--text-tertiary)]">{(r.duration_ms / 1000).toFixed(1)}s</span>}
                <span className="text-[var(--text-tertiary)]">{r.capabilities_passed}/{r.capabilities_run} passed</span>
                {r.capabilities_failed > 0 && <span className="text-red-400">{r.capabilities_failed} failed</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Compatibility Aliases */}
      <div className="rounded border border-[var(--border-subtle)] bg-[var(--surface-base)] p-3">
        <div className="text-xs font-semibold text-[var(--text-primary)] mb-2 flex items-center gap-1">
          <RotateCcw className="h-3 w-3 text-slate-400" />
          Compatibility Aliases (legacy → canonical)
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-1 text-xs">
          {COMPAT_ALIASES.map((a) => (
            <div key={a.alias} className="flex items-center gap-1 p-1 rounded bg-[var(--surface-raised)]">
              <span className="font-mono text-[var(--text-tertiary)]">{a.alias}</span>
              <span className="text-[var(--text-tertiary)]">→</span>
              <span className="font-mono text-violet-400">{a.canonical}</span>
              <span className="text-[var(--text-tertiary)] text-[10px]">({a.note})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function CommandVocabularyPanel() {
  return (
    <div className="rounded border border-[var(--border-subtle)] bg-[var(--surface-base)] p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
          <Terminal className="h-4 w-4 text-violet-400" />
          Canonical Command Vocabulary (C63 §9)
        </div>
        <span className="text-xs text-[var(--text-tertiary)] font-mono">9 commands</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {CANONICAL_COMMANDS.map((cmd) => (
          <CommandCard key={cmd.id} cmd={cmd} />
        ))}
      </div>
      <div className="text-xs text-[var(--text-tertiary)] border-t border-[var(--border-subtle)] pt-2 mt-2">
        UI
         ↓
        Platform API
         ↓
        canonical control plane
         ↓
        canonical executor
        <br />
        <span className="text-red-400">Never: UI → executor (bypassing control plane)</span>
      </div>
    </div>
  );
}

function CommandCard({ cmd }: { cmd: typeof CANONICAL_COMMANDS[0] }) {
  const Icon = cmd.icon;
  return (
    <div className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] hover:border-[var(--border-default)] transition-colors">
      <div className="flex items-center gap-2 mb-1">
        <Icon className={cn('h-4 w-4', cmd.color)} />
        <span className="font-mono text-sm font-semibold text-[var(--text-primary)]">{cmd.label}</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--surface-base)] text-[var(--text-tertiary)] uppercase">{cmd.id}</span>
      </div>
      <div className="text-xs text-[var(--text-tertiary)] ml-6">{cmd.description}</div>
    </div>
  );
}

function RecommendationPanel({ recommendation }: { recommendation: { recommended: string[]; rationale: string } }) {
  if (!recommendation.recommended.length) return null;

  return (
    <div className="rounded border border-emerald-500/30 bg-emerald-500/5 p-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-emerald-400 mb-2">
        <Zap className="h-4 w-4" />
        Verification Recommendation
      </div>
      <div className="text-xs text-[var(--text-secondary)] mb-2">{recommendation.rationale}</div>
      <div className="flex flex-wrap gap-1">
        {recommendation.recommended.slice(0, 8).map((cap) => (
          <Link
            key={cap}
            href={`/platform/verification/${encodeURIComponent(cap)}`}
            className="text-xs font-mono px-2 py-1 rounded bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 transition-colors"
          >
            {cap}
          </Link>
        ))}
        {recommendation.recommended.length > 8 && (
          <span className="text-xs text-[var(--text-tertiary)]">+{recommendation.recommended.length - 8} more</span>
        )}
      </div>
    </div>
  );
}

function CapabilityRow({ cap, onRun, recentRuns }: { cap: { id: string; name: string; stage: string; cost: string; authorization: string; produces: string[]; triggers: string[] }; onRun: () => void; recentRuns: Array<{ id: string; status: string; started_at: string; duration_ms: number | null; capabilities_run: number; capabilities_passed: number; capabilities_failed: number }> }) {
  // Find last run for this capability
  const lastRun = recentRuns.find((r) => r.id.includes(cap.id) || r.id.includes(cap.id.replace('.', '-')));
  const lastRunStatus = lastRun?.status ?? 'NEVER';
  const lastRunTime = lastRun?.started_at ?? '—';
  const lastRunDuration = lastRun?.duration_ms ? `${(lastRun.duration_ms / 1000).toFixed(1)}s` : '—';
  const lastRunEvidence = lastRun && lastRun.capabilities_run > 0 ? '✓' : '—';

  return (
    <tr className="border-t border-[var(--border-subtle)]">
      <td className="p-2">
        <Link className="text-[var(--text-primary)] hover:underline" href={`/platform/verification/${encodeURIComponent(cap.id)}`}>
          {cap.id}
        </Link>
        <div className="text-[var(--text-tertiary)] text-[10px]">{cap.name}</div>
      </td>
      <td className="p-2">{String(cap.stage)}</td>
      <td className="p-2">{String(cap.cost)}</td>
      <td className="p-2">{String(cap.authorization)}</td>
      <td className="p-2">
        <HealthBadge status={lastRunStatus === 'HEALTHY' || lastRunStatus === 'CLOSED' ? 'HEALTHY' : lastRunStatus === 'UNHEALTHY' || lastRunStatus === 'FAILED' ? 'UNHEALTHY' : lastRunStatus === 'DEGRAD' ? 'DEGRAD' : 'UNKNOWN'} size="sm" showLabel={false} />
        <span className="ml-1 text-[10px] text-[var(--text-tertiary)] font-mono">{lastRunTime.slice(0, 16)}</span>
      </td>
      <td className="p-2 text-[var(--text-tertiary)] font-mono">{lastRunDuration}</td>
      <td className="p-2 text-center text-[var(--text-tertiary)]">{lastRunEvidence}</td>
      <td className="p-2">
        <button
          className="px-2 py-1 rounded border border-[var(--border-subtle)] hover:bg-[var(--surface-raised)] transition-colors"
          onClick={onRun}
        >
          Run
        </button>
      </td>
    </tr>
  );
}