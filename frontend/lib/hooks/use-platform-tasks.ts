/**
 * Platform Tasks Hook — M9-C63
 *
 * Fetches task/obligation counts from /platform/v1/tasks.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetchJson } from '@/lib/api/gateway';

export interface TaskItem {
  id: string;
  name: string;
  capability_id: string;
  status: string;
  created_at: string;
  closed_at: string | null;
}

export interface TaskListData {
  open_count: number;
  closed_count: number;
  items: TaskItem[];
}

export interface TaskListResponse {
  kind: string;
  version: string;
  generated_at: string;
  id: string;
  data: TaskListData;
}

const STALE_TIME_MS = 60_000;

export function useTaskList() {
  return useQuery<TaskListResponse, Error>({
    queryKey: ['platform', 'tasks'],
    queryFn: () => apiFetchJson('/platform/v1/tasks') as Promise<TaskListResponse>,
    staleTime: STALE_TIME_MS,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('4')) return false;
      return failureCount < 2;
    },
  });
}

export function useOpenObligationsCount() {
  const { data } = useTaskList();
  return data?.data?.open_count ?? 0;
}

export function useClosedObligationsCount() {
  const { data } = useTaskList();
  return data?.data?.closed_count ?? 0;
}