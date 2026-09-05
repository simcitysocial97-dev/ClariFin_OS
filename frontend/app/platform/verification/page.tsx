/**
 * Verification Center — M9-C57 Phase 6
 *
 * Roadmap requirements:
 *   capability, profile, status, last run, duration, evidence, action
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
import { useCapabilities, useRecentVerificationRuns, useVerificationRun, useVerificationRunAffected, useVerificationRunFull, useVerificationRunGroup } from '@/lib/hooks/use-verification-center';

export default function VerificationCenterPage() {
  const caps = useCapabilities();
  const recent = useRecentVerificationRuns(20);
  const runOne = useVerificationRun();
  const runGroup = useVerificationRunGroup();
  const runAffected = useVerificationRunAffected();
  const runFull = useVerificationRunFull();

  const [filterStage, setFilterStage] = useState<string>('all');
  const [runResult, setRunResult] = useState<string | null>(null);

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Verification Center</h1>
          <p className="text-sm text-[var(--text-tertiary)]">Capabilities · Profiles · Evidence · Runs</p>
        </div>
        <div className="flex gap-2">
          <button
            className="px-3 py-1 rounded border border-[var(--border-subtle)] text-xs bg-[var(--surface-raised)]"
            onClick={() => void mutate('affected')}
          >
            Run affected
          </button>
          <button
            className="px-3 py-1 rounded border border-[var(--border-subtle)] text-xs bg-[var(--surface-raised)]"
            onClick={() => void mutate('full')}
          >
            Run full
          </button>
        </div>
      </div>

      {runResult && <div className="text-xs font-mono text-[var(--text-secondary)] border border-[var(--border-subtle)] p-2 rounded">{runResult}</div>}

      <div className="flex gap-2 text-xs">
        <button className={`px-2 py-1 rounded ${filterStage === 'all' ? 'bg-[var(--surface-raised)]' : ''}`} onClick={() => setFilterStage('all')}>
          All ({caps.data?.data?.count ?? 0})
        </button>
        {categories.map((c) => (
          <button
            key={c}
            className={`px-2 py-1 rounded ${filterStage === c ? 'bg-[var(--surface-raised)]' : ''}`}
            onClick={() => setFilterStage(c)}
          >
            {c}
          </button>
        ))}
      </div>

      <div className="rounded border border-[var(--border-subtle)] overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-[var(--surface-raised)] text-[var(--text-tertiary)]">
            <tr>
              <th className="text-left p-2">Capability</th>
              <th className="text-left p-2">Stage</th>
              <th className="text-left p-2">Cost</th>
              <th className="text-left p-2">Auth</th>
              <th className="text-left p-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {caps.isLoading ? (
              <tr>
                <td className="p-2 text-[var(--text-tertiary)]" colSpan={5}>
                  Loading…
                </td>
              </tr>
            ) : (
              filtered.map((it) => (
                <tr key={it.id} className="border-t border-[var(--border-subtle)]">
                  <td className="p-2">
                    <Link className="text-[var(--text-primary)] hover:underline" href={`/platform/verification/${encodeURIComponent(it.id)}`}>
                      {it.id}
                    </Link>
                    <div className="text-[var(--text-tertiary)] text-[10px]">{it.name}</div>
                  </td>
                  <td className="p-2">{String(it.stage)}</td>
                  <td className="p-2">{String(it.cost)}</td>
                  <td className="p-2">{String(it.authorization)}</td>
                  <td className="p-2">
                    <button
                      className="px-2 py-1 rounded border border-[var(--border-subtle)]"
                      onClick={() => void mutate('run', { capability_id: it.id })}
                    >
                      Run
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {recent.data && (
        <div className="rounded border border-[var(--border-subtle)] p-3">
          <div className="text-xs font-semibold text-[var(--text-primary)] mb-2">Recent runs</div>
          <div className="text-xs text-[var(--text-secondary)]">
            Showing {recent.data.data.items.length} of {recent.data.data.count}
          </div>
          <ul className="text-xs font-mono">
            {recent.data.data.items.slice(0, 10).map((r) => (
              <li key={r.id}>
                {r.id} — {String(r.status)} — {r.started_at}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
