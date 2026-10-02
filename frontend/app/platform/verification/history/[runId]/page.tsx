'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { apiFetchJson, transientRetryPolicy } from '@/lib/api/gateway';
import { describeError } from '@/lib/api/errors';
import { ConsoleEmptyState, ConsoleUnavailableState } from '@/components/platform/console-state';
import { RefreshCw } from 'lucide-react';

export default function RunHistoryPage() {
  const params = useParams<{ runId: string }>();
  const runId = String(params?.runId ?? '');
  const q = useQuery({
    queryKey: ['platform', 'run', runId],
    queryFn: () =>
      apiFetchJson(`/platform/v1/history/runs/${runId}`) as Promise<unknown>,
    enabled: !!runId,
    retry: transientRetryPolicy,
  });

  if (q.isError) {
    // M10-A3: this rendered `JSON.stringify(q.error, null, 2)`, dumping the
    // stringified `ApiError` — status, transient flag, and the fully escaped
    // response envelope — into a <pre> as the entire page body. A missing run
    // (the common case: a stale bookmark or a link from another tool) produced
    // a screen of raw JSON. The authority's own message is now surfaced through
    // the console's standard terminal state, with a retry.
    return (
      <ConsoleUnavailableState
        heading={`Run ${runId}`}
        subject="This run cannot be read from the EngineeringEventStore, so no run detail can be reported."
        message={describeError(q.error)}
        onRetry={() => void q.refetch()}
      />
    );
  }

  if (!q.data) {
    return (
      <ConsoleEmptyState
        heading={`Run ${runId}`}
        subject="No run record returned"
        detail="The platform API answered without a run record for this identifier."
        action={
          <button
            type="button"
            onClick={() => void q.refetch()}
            className="mt-1 inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-sm text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-raised)]"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Retry
          </button>
        }
      />
    );
  }

  return (
    <div className="flex flex-col gap-3 max-w-3xl">
      <div className="flex items-center gap-2">
        <Link href="/platform/verification" className="text-xs text-[var(--text-tertiary)] underline">
          ← Verification Center
        </Link>
      </div>
      <h1 className="text-lg font-bold">Run {runId}</h1>
      <pre className="text-xs font-mono whitespace-pre-wrap border border-[var(--border-subtle)] p-2 rounded max-h-[70vh] overflow-auto">
        {q.isLoading ? 'Loading…' : JSON.stringify(q.data, null, 2)}
      </pre>
    </div>
  );
}
