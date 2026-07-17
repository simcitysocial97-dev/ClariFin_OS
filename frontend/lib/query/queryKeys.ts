/**
 * Query Key Factory — Centralized, strongly-typed React Query keys
 *
 * All query keys are organized by capability and return readonly tuples.
 * Keys are deterministic and never duplicated as strings.
 */

export const queryKeys = {
  // Financial Health capability
  financialHealth: {
    summary: () => ['financialHealth', 'summary'] as const,
  },

  // Cashflow capability
  cashflow: {
    monthly: (months: number = 6) => ['cashflow', 'monthly', months] as const,
  },

  // Transaction Intelligence capability
  transactions: {
    list: (filters?: Record<string, unknown>) => ['transactions', 'list', filters] as const,
  },

  // Account Management capability
  accounts: {
    managed: () => ['accounts', 'managed'] as const,
    computed: () => ['accounts', 'computed'] as const,
  },

  // Credit Cards capability
  cards: {
    list: () => ['cards', 'list'] as const,
  },

  // Debt Management capability
  loans: {
    list: () => ['loans', 'list'] as const,
    schedule: (id: string | null) => ['loans', 'schedule', id] as const,
    prepayment: (
      id: string | null,
      prepaymentPaise: number,
      mode: 'reduce_tenure' | 'reduce_emi',
    ) => ['loans', 'prepayment', id, prepaymentPaise, mode] as const,
  },

  // Reconciliation capability
  reconciliation: {
    pending: () => ['reconciliation', 'pending'] as const,
    list: () => ['reconciliation', 'list'] as const,
    scan: () => ['reconciliation', 'scan'] as const,
  },

  // Behavior capability
  behavior: {
    score: () => ['behavior', 'score'] as const,
    insights: () => ['behavior', 'insights'] as const,
  },

  // Analytics capability
  analytics: {
    overview: () => ['analytics', 'overview'] as const,
  },

  // Investments capability
  investments: {
    list: () => ['investments', 'list'] as const,
  },

  // Overview (legacy - for compatibility)
  overview: (params?: Record<string, unknown>) => ['overview', params] as const,

  // NetWorth (legacy - for compatibility)
  networth: {
    current: () => ['networth', 'current'] as const,
  },
} as const

// Type helper for query key inference
export type QueryKey<T extends (...args: never) => readonly unknown[]> = ReturnType<T>
