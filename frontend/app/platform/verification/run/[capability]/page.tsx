'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState, useCallback, useTransition } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';
import { useLiveExecution } from '@/lib/hooks/use-live-execution';

type ExecutionDetail = {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: {
    id: string;
    task_id: string;
    capability_id: string;
    status: string;
    started_at: string;
    finished_at: string | null;
    phase: string;
    current_state: string;
    events: string[];
    stdout_ref: string | null;
    stderr_ref: string | null;
    evidence_ids: string[];
    decision_id: string | null;
  };
};

type StreamEvent = {
  kind: string;
  data: {
    execution_id: string;
    event_type: string;
    payload: Record<string, unknown>;
    emitted_at: string;
  };
};

export default function LiveExecutionPage() {
  const params = useParams<{ capability: string }>();
  const capId = decodeURIComponent(String(params?.capability ?? ''));

  const [executionId, setExecutionId] = useState<string | null>(null);
  const [_isPending, startTransition] = useTransition();
  const [runSubmitted, setRunSubmitted] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Submit the verification run and capture the execution_id.
  const submitRun = useCallback(async () => {
    if (!capId || runSubmitted) return;
    setRunSubmitted(true);
    try {
      const res = await fetch(`/platform/v1/verification/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ capability_id: capId }),
      });
      const json = (await res.json()) as { kind: string; data: { execution_id?: string; task_id?: string } };
      const eid = json?.data?.execution_id ?? json?.data?.task_id ?? null;
      if (eid) {
        setExecutionId(eid);
      } else {
        setSubmitError('No execution_id returned from run');
        setRunSubmitted(false);
      }
    } catch (e: unknown) {
      setSubmitError(String(e));
      setRunSubmitted(false);
    }
  }, [capId, runSubmitted]);

  // Fetch execution detail once we have an executionId.
  const detailQuery = useQuery({
    queryKey: ['platform', 'execution', executionId],
    queryFn: () =>
      apiFetchJson(`/platform/v1/executions/${encodeURIComponent(executionId!)}`) as Promise<ExecutionDetail>,
    enabled: !!executionId,
    refetchOnWindowFocus: false,
  });

  // Live SSE stream.
  const { events, state, completionReason } = useLiveExecution({
    executionId,
    onComplete: () => {
      // Detail is final — no need to refetch.
    },
  });

  // Auto-submit on mount when a capability is provided.
  useEffect(() => {
    if (capId && !runSubmitted) {
      startTransition(() => {
        void submitRun();
      });
    }
  }, [capId, runSubmitted, submitRun]);

  const data = detailQuery.data?.data;

  return (
    <div className="flex flex-col gap-4 max-w-4xl">
      <div className="flex items-center gap-2">
        <Link href="/platform/verification" className="text-xs text-[var(--text-tertiary)] underline">
          ← Verification Center
        </Link>
      </div>

      <div className="flex items-baseline gap-3">
        <h1 className="text-lg font-bold">Live execution</h1>
        <span className="text-xs text-[var(--text-tertiary)]">{capId || 'all'}</span>
      </div>

      {/* Execution meta */}
      {data && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-[var(--text-tertiary)]">Task: </span>
            <span className="font-mono">{data.task_id}</span>
          </div>
          <div>
            <span className="text-[var(--text-tertiary)]">Phase: </span>
            <span>{data.phase}</span>
          </div>
          <div>
            <span className="text-[var(--text-tertiary)]">Status: </span>
            <StatusBadge status={data.status} />
          </div>
          <div>
            <span className="text-[var(--text-tertiary)]">State: </span>
            <span className="font-mono text-xs">{data.current_state}</span>
          </div>
          <div>
            <span className="text-[var(--text-tertiary)]">Started: </span>
            <span className="font-mono text-xs">{data.started_at}</span>
          </div>
          {data.finished_at && (
            <div>
              <span className="text-[var(--text-tertiary)]">Finished: </span>
              <span className="font-mono text-xs">{data.finished_at}</span>
            </div>
          )}
          {data.evidence_ids.length > 0 && (
            <div className="col-span-2">
              <span className="text-[var(--text-tertiary)]">Evidence: </span>
              {data.evidence_ids.map((eid) => (
                <span key={eid} className="font-mono text-xs mr-2">
                  {eid}
                </span>
              ))}
            </div>
          )}
          {data.decision_id && (
            <div>
              <span className="text-[var(--text-tertiary)]">Decision: </span>
              <span className="font-mono text-xs">{data.decision_id}</span>
            </div>
          )}
        </div>
      )}

      {/* SSE connection state — NO synthetic progress bar */}
      <div className="text-xs text-[var(--text-tertiary)]">
        {state === 'connecting' && 'Connecting to event stream…'}
        {state === 'active' && `Stream active — ${events.length} event(s) received`}
        {state === 'complete' && `Stream complete (${completionReason})`}
        {state === 'error' && 'Stream error — check backend connectivity'}
      </div>

      {/* Event timeline */}
      <div className="border border-[var(--border-subtle)] rounded p-3">
        <div className="text-xs font-semibold mb-2 text-[var(--text-secondary)]">Event timeline</div>
        {events.length === 0 && state !== 'complete' ? (
          <div className="text-xs text-[var(--text-tertiary)] italic">Waiting for events…</div>
        ) : (
          <div className="flex flex-col gap-1">
            {events.map((ev, idx) => (
              <EventRow key={`${ev.id}-${idx}`} event={ev} />
            ))}
          </div>
        )}
      </div>

      {/* Submitted-but-not-yet-yielded-execution state */}
      {!executionId && !submitError && (
        <div className="text-xs text-[var(--text-tertiary)]">Submitting verification run…</div>
      )}
      {submitError && (
        <div className="text-xs text-red-500">Error: {submitError}</div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === 'CLOSED' || status === 'HEALTHY'
      ? 'text-green-600'
      : status === 'OPEN' || status === 'DEGRAD'
        ? 'text-yellow-600'
        : 'text-red-600';
  return <span className={`font-semibold ${color}`}>{status}</span>;
}

function EventRow({ event }: { event: StreamEvent }) {
  const payload = event.data.payload as Record<string, unknown>;
  return (
    <div className="flex gap-2 text-xs font-mono border-b border-[var(--border-subtle)] pb-1">
      <span className="text-[var(--text-tertiary)] shrink-0">{event.data.emitted_at}</span>
      <span className="font-semibold shrink-0">{event.data.event_type}</span>
      <span className="text-[var(--text-secondary)] break-all">
        {Object.entries(payload)
          .slice(0, 4)
          .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
          .join(' ')}
      </span>
    </div>
  );
}
