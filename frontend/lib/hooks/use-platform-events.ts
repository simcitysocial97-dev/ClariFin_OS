/**
 * Platform Events Hook — M9-C57 Phase 5
 *
 * Fetches recent events from /platform/v1/events.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

export interface PlatformEvent {
  id: string;
  event_type: string;
  task_id?: string;
  execution_id?: string;
  capability_id?: string;
  emitted_at: string;
  payload?: Record<string, unknown>;
}

export interface EventsListData {
  window: string;
  count: number;
  items: PlatformEvent[];
}

export interface EventsListResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: EventsListData;
}

export function usePlatformEvents(limit = 20) {
  return useQuery<EventsListResponse, Error>({
    queryKey: ['platform', 'events', limit],
    queryFn: () =>
      apiFetchJson(`/platform/v1/events?limit=${limit}`) as Promise<EventsListResponse>,
    staleTime: 30_000,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}
