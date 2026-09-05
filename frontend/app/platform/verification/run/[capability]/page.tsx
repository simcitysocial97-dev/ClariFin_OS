'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function LiveExecutionPage() {
  const params = useParams<{ capability: string }>();
  const capId = decodeURIComponent(String(params?.capability ?? ''));
  const [log, setLog] = useState<string[]>([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!capId) return;
    setRunning(true);
    const ctrl = new AbortController();
    fetch(`/platform/v1/verification/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ capability_id: capId }),
      signal: ctrl.signal,
    })
      .then(async (r) => {
        const j = await r.json();
        setLog((l) => [...l, JSON.stringify(j, null, 2)]);
        const execId = j?.data?.execution_id ?? j?.data?.task_id ?? null;
        if (execId) {
          const es = new EventSource(`/platform/v1/executions/${encodeURIComponent(execId)}/stream`);
          es.onmessage = (ev) => setLog((l) => [...l, ev.data]);
          es.addEventListener('end', () => es.close());
          es.onerror = () => es.close();
          ctrl.signal.addEventListener('abort', () => es.close(), { once: true });
        }
        setRunning(false);
      })
      .catch((e: unknown) => {
        setLog((l) => [...l, String(e)]);
        setRunning(false);
      });
    return () => ctrl.abort();
  }, [capId]);

  return (
    <div className="flex flex-col gap-3 max-w-3xl">
      <div className="flex items-center gap-2">
        <Link href="/platform/verification" className="text-xs text-[var(--text-tertiary)] underline">
          ← Verification Center
        </Link>
      </div>
      <h1 className="text-lg font-bold">Live execution — {capId || 'all'}</h1>
      <div className="text-xs text-[var(--text-tertiary)]">{running ? 'Running…' : 'Done'}</div>
      <pre className="text-xs font-mono whitespace-pre-wrap border border-[var(--border-subtle)] p-2 rounded max-h-[60vh] overflow-auto">
        {log.join('\n') || 'No output yet'}
      </pre>
    </div>
  );
}
