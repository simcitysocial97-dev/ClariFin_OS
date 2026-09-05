'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useCapabilityDetail, useVerificationRun } from '@/lib/hooks/use-verification-center';
import { useState } from 'react';

export default function CapabilityDetailPage() {
  const params = useParams<{ capability: string }>();
  const capId = decodeURIComponent(String(params?.capability ?? ''));
  const detail = useCapabilityDetail(capId);
  const runOne = useVerificationRun();
  const [msg, setMsg] = useState<string | null>(null);

  const onRun = async () => {
    try {
      const res = await runOne.mutateAsync({ capability_id: capId });
      setMsg(`${res.kind} · ${res.data.message}`);
    } catch (e: unknown) {
      setMsg(String((e as Error)?.message ?? e));
    }
  };

  if (!capId) return <div className="text-xs text-[var(--text-tertiary)]">Missing capability</div>;
  if (detail.isLoading) return <div className="text-xs text-[var(--text-tertiary)]">Loading {capId}…</div>;
  if (detail.isError) return <div className="text-xs text-red-400">Failed: {String(detail.error)}</div>;
  const d = detail.data?.data;
  if (!d) return <div className="text-xs text-[var(--text-tertiary)]">No data for {capId}</div>;

  return (
    <div className="flex flex-col gap-3 max-w-3xl">
      <div className="flex items-center gap-2">
        <Link href="/platform/verification" className="text-xs text-[var(--text-tertiary)] underline">
          ← Verification Center
        </Link>
      </div>
      <h1 className="text-lg font-bold">{d.id}</h1>
      <div className="text-xs text-[var(--text-secondary)]">{d.name}</div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-[var(--text-tertiary)]">Owner:</span> {d.owner}
        </div>
        <div>
          <span className="text-[var(--text-tertiary)]">Stage:</span> {String(d.stage)}
        </div>
        <div>
          <span className="text-[var(--text-tertiary)]">Command:</span> <span className="font-mono">{d.command ?? '—'}</span>
        </div>
        <div>
          <span className="text-[var(--text-tertiary)]">Health:</span> {d.health}
        </div>
        <div>
          <span className="text-[var(--text-tertiary)]">Cache:</span> {d.cache_status ?? '—'}
        </div>
      </div>
      <div className="flex gap-2">
        <button className="px-3 py-1 rounded border border-[var(--border-subtle)] text-xs" onClick={() => void onRun()}>
          Run
        </button>
        <Link className="px-3 py-1 rounded border border-[var(--border-subtle)] text-xs" href={`/platform/verification/run/${encodeURIComponent(capId)}`}>
          Live execution
        </Link>
      </div>
      {msg && <div className="text-xs font-mono border border-[var(--border-subtle)] p-2 rounded">{msg}</div>}
      <div className="text-xs">
        <div className="font-semibold">Dependencies</div>
        <div className="font-mono">{d.dependencies.length ? d.dependencies.join(', ') : '—'}</div>
      </div>
      <div className="text-xs">
        <div className="font-semibold">Produces</div>
        <div className="font-mono">{d.produces.length ? d.produces.join(', ') : '—'}</div>
      </div>
      <div className="text-xs">
        <div className="font-semibold">Recent executions</div>
        <div className="font-mono">{d.recent_executions.length ? d.recent_executions.join(', ') : '—'}</div>
      </div>
      <div className="text-xs">
        <div className="font-semibold">Evidence</div>
        <div className="font-mono">{d.evidence.length ? d.evidence.join(', ') : '—'}</div>
      </div>
    </div>
  );
}
