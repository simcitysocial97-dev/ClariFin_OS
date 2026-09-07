/**
 * Live execution SSE hook — M9-C57 Phase 7
 *
 * Connects to /platform/v1/executions/{executionId}/stream and emits
 * structured events as they arrive. Detects terminal completion via the
 * ``event: complete`` SSE event. No synthetic progress percentage.
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export type ExecutionStreamEvent = {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: {
    execution_id: string;
    event_type: string;
    payload: Record<string, unknown>;
    emitted_at: string;
  };
};

export type StreamState = 'connecting' | 'active' | 'complete' | 'error';

export interface UseLiveExecutionOptions {
  executionId: string | null;
  onEvent?: (event: ExecutionStreamEvent) => void;
  onComplete?: (reason: string) => void;
  onError?: (error: unknown) => void;
}

export function useLiveExecution({
  executionId,
  onEvent,
  onComplete,
  onError,
}: UseLiveExecutionOptions) {
  const [events, setEvents] = useState<ExecutionStreamEvent[]>([]);
  const [state, setState] = useState<StreamState>('connecting');
  const [completionReason, setCompletionReason] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const close = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!executionId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setState('connecting');
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setEvents([]);
      return;
    }

    const url = `/platform/v1/executions/${encodeURIComponent(executionId)}/stream`;
    const es = new EventSource(url);
    esRef.current = es;

    setState('active');
    setEvents([]);
    setCompletionReason(null);

    es.onmessage = (ev: MessageEvent) => {
      try {
        const parsed = JSON.parse(ev.data) as ExecutionStreamEvent;
        setEvents((prev) => [...prev, parsed]);
        onEvent?.(parsed);
      } catch {
        // Non-JSON message — ignore (could be a comment)
      }
    };

    es.addEventListener('complete', (ev: Event) => {
      const messageEvent = ev as MessageEvent;
      let reason = 'unknown';
      try {
        const parsed = JSON.parse(messageEvent.data as string) as { reason?: string };
        reason = parsed.reason ?? 'unknown';
      } catch {
        // ignore
      }
      setCompletionReason(reason);
      setState('complete');
      onComplete?.(reason);
    });

    es.onerror = () => {
      setState('error');
      onError?.(new Error('SSE connection error'));
      es.close();
    };

    return () => {
      close();
    };
  }, [executionId, onEvent, onComplete, onError, close]);

  return { events, state, completionReason, close };
}
