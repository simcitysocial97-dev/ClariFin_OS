/**
 * Navigation State Persistence - Stage 3 Transaction Intelligence Workspace
 *
 * Utilities for persisting navigation state in URL.
 */

import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useCallback } from 'react';

/**
 * Navigation state stored in URL
 */
export interface NavigationState {
  category?: string;
  merchant?: string;
  date?: string;
  month?: string;
  account?: string;
  balance?: string;
  reconciliation?: string;
  import?: string;
  adjustment?: string;
}

/**
 * Hook to get current navigation state from URL
 */
export function useNavigationState(): NavigationState {
  const searchParams = useSearchParams();

  return {
    category: searchParams.get('category') ?? undefined,
    merchant: searchParams.get('merchant') ?? undefined,
    date: searchParams.get('date') ?? undefined,
    month: searchParams.get('month') ?? undefined,
    account: searchParams.get('account') ?? undefined,
    balance: searchParams.get('balance') ?? undefined,
    reconciliation: searchParams.get('reconciliation') ?? undefined,
    import: searchParams.get('import') ?? undefined,
    adjustment: searchParams.get('adjustment') ?? undefined,
  };
}

/**
 * Hook to set navigation state in URL
 */
export function useSetNavigationState(): (state: Partial<NavigationState>) => void {
  const router = useRouter();
  const pathname = usePathname();

  return useCallback(
    (state: Partial<NavigationState>) => {
      const searchParams = new URLSearchParams();

      // Preserve existing params
      const currentParams = new URLSearchParams(window.location.search);
      currentParams.forEach((value, key) => {
        if (!Object.keys(state).includes(key)) {
          searchParams.set(key, value);
        }
      });

      // Set new state
      Object.entries(state).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.set(key, value);
        } else {
          searchParams.delete(key);
        }
      });

      const queryString = searchParams.toString();
      const newUrl = queryString ? `${pathname}?${queryString}` : pathname;

      router.push(newUrl);
    },
    [router, pathname]
  );
}

/**
 * Hook to clear navigation state from URL
 */
export function useClearNavigationState(): () => void {
  const router = useRouter();
  const pathname = usePathname();

  return useCallback(() => {
    router.push(pathname);
  }, [router, pathname]);
}

/**
 * Get navigation state from URL string
 */
export function parseNavigationState(url: string): NavigationState {
  const searchParams = new URLSearchParams(url.split('?')[1] || '');

  return {
    category: searchParams.get('category') ?? undefined,
    merchant: searchParams.get('merchant') ?? undefined,
    date: searchParams.get('date') ?? undefined,
    month: searchParams.get('month') ?? undefined,
    account: searchParams.get('account') ?? undefined,
    balance: searchParams.get('balance') ?? undefined,
    reconciliation: searchParams.get('reconciliation') ?? undefined,
    import: searchParams.get('import') ?? undefined,
    adjustment: searchParams.get('adjustment') ?? undefined,
  };
}

/**
 * Build URL with navigation state
 */
export function buildNavigationUrl(
  base: string,
  state: NavigationState
): string {
  const searchParams = new URLSearchParams();

  Object.entries(state).forEach(([key, value]) => {
    if (value !== undefined) {
      searchParams.set(key, value);
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `${base}?${queryString}` : base;
}