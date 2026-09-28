'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

export default function RunHistoryPage() {
  const params = useParams<{ runId: string }>();
  const runId = String(params?.runId ?? '');
  const q = useQuery({
    queryKey: ['platform', 'run', runId],
    queryFn: () => apiFetchJson(`/platform/v1/history/runs/${runId}`) as Promise<unknown>,
    enabled: !!runId,
  });

  return (
    <div className="flex flex-col gap-3 max-w-3xl">
      <div className="flex items-center gap-2">
        <Link href="/platform/verification" className="text-xs text-[var(--text-tertiary)] underline">
          ← Verification Center
        </Link>
      </div>
      <h1 className="text-lg font-bold">Run {runId}</h1>
      <pre className="text-xs font-mono whitespace-pre-wrap border border-[var(--border-subtle)] p-2 rounded max-h-[70vh] overflow-auto">
        {q.isLoading ? 'Loading…' : JSON.stringify(q.data, null, 2) ?? JSON.stringify(q.error, null, 2)}
      </pre>
    </div>
  );
}
