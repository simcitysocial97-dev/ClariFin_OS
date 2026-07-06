import { useQueryClient } from '@tanstack/react-query';
import {
  fetchOverview,
  fetchBehaviorScore,
} from '@/lib/api/client';
import type { OverviewData, BehaviorScore } from '@/lib/api/client';
import { useAsyncQuery, HookState } from './use-async-query';

export const queryKeys = {
  overview: ['overview'] as const,
  behaviorScore: ['behavior', 'score'] as const,
};

type FinanceQueryFactory<T, Args extends any[] = []> = (...args: Args) => HookState<T>;

function createFinanceQuery<T, Args extends any[] = []>(factory: (...args: Args) => HookState<T>): FinanceQueryFactory<T, Args> {
  return factory;
}

export const useOverviewQuery = createFinanceQuery<OverviewData>(() => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<OverviewData>(queryKeys.overview, fetchOverview);

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.overview });
  };

  return { ...result, refetch };
});

export const useBehaviorScoreQuery = createFinanceQuery<BehaviorScore>(() => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<BehaviorScore>(queryKeys.behaviorScore, fetchBehaviorScore);

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.behaviorScore });
  };

  return { ...result, refetch };
});