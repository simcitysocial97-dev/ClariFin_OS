/**
 * useNetWorthCapability Tests - Stage 4 Net Worth Intelligence Workspace
 *
 * Unit tests for the net worth capability hook.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useNetWorthCapability } from '../use-net-worth-capability';
import { netWorthMapper } from '@/lib/mappers/net-worth-mapper';

// Mock the mapper
vi.mock('@/lib/mappers/net-worth-mapper', () => ({
  netWorthMapper: {
    mapNetWorthDTO: vi.fn(),
  },
}));

// Mock React Query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}));

describe('useNetWorthCapability', () => {
  const mockMapNetWorthDTO = vi.mocked(netWorthMapper.mapNetWorthDTO);

  beforeEach(() => {
    vi.clearAllMocks();
    mockMapNetWorthDTO.mockReturnValue({
      total_net_worth_paise: 15000000,
      total_assets_paise: 20000000,
      total_liabilities_paise: 5000000,
      composition: {
        total_assets_paise: 20000000,
        total_liabilities_paise: 5000000,
        asset_breakdown: [],
        liability_breakdown: [],
      },
      insights: [],
      filters: {
        date_range: undefined,
        account_types: undefined,
        period: undefined,
      },
      navigation: {
        deep_link: '/net-worth',
        cross_references: {},
      },
    });
  });

  it('should return initial state with default values', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    expect(result.current.netWorth).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.dateRange).toBeNull();
    expect(result.current.accountTypes).toEqual([]);
    expect(result.current.period).toBe('1M');
    expect(result.current.isEvidenceDrawerOpen).toBe(false);
    expect(result.current.loadingTimeout).toBe(false);
    expect(result.current.loadingTimeoutMessage).toBe('');
    expect(result.current.errorRecoveryAttempts).toBe(0);
    expect(result.current.isRecovering).toBe(false);
  });

  it('should have all required action functions', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    // Fetch actions
    expect(typeof result.current.fetchNetWorth).toBe('function');
    expect(typeof result.current.refresh).toBe('function');
    expect(typeof result.current.recoverFromError).toBe('function');

    // Filter actions
    expect(typeof result.current.setDateRange).toBe('function');
    expect(typeof result.current.setAccountTypes).toBe('function');
    expect(typeof result.current.setPeriod).toBe('function');
    expect(typeof result.current.clearFilters).toBe('function');
    expect(typeof result.current.applyFilters).toBe('function');

    // Evidence drawer
    expect(typeof result.current.toggleEvidenceDrawer).toBe('function');
  });

  it('should update date range filter', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    act(() => {
      result.current.setDateRange({ from: '2026-01-01', to: '2026-12-31' });
    });

    expect(result.current.dateRange).toEqual({ from: '2026-01-01', to: '2026-12-31' });
  });

  it('should update account types filter', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    act(() => {
      result.current.setAccountTypes(['savings', 'current']);
    });

    expect(result.current.accountTypes).toEqual(['savings', 'current']);
  });

  it('should update period filter', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    act(() => {
      result.current.setPeriod('3M');
    });

    expect(result.current.period).toBe('3M');
  });

  it('should clear all filters', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    // Set some filters first
    act(() => {
      result.current.setDateRange({ from: '2026-01-01', to: '2026-12-31' });
      result.current.setAccountTypes(['savings']);
      result.current.setPeriod('3M');
    });

    // Clear filters
    act(() => {
      result.current.clearFilters();
    });

    expect(result.current.dateRange).toBeNull();
    expect(result.current.accountTypes).toEqual([]);
    expect(result.current.period).toBe('1M');
  });

  it('should toggle evidence drawer', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    act(() => {
      result.current.toggleEvidenceDrawer();
    });

    expect(result.current.isEvidenceDrawerOpen).toBe(true);

    act(() => {
      result.current.toggleEvidenceDrawer();
    });

    expect(result.current.isEvidenceDrawerOpen).toBe(false);
  });

  it('should increment error recovery attempts on recoverFromError', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    act(() => {
      result.current.recoverFromError();
    });

    expect(result.current.errorRecoveryAttempts).toBe(1);
  });

  it('should not exceed max recovery attempts', () => {
    const { result } = renderHook(() => useNetWorthCapability());

    // Set to max attempts
    act(() => {
      result.current.recoverFromError();
      result.current.recoverFromError();
      result.current.recoverFromError();
    });

    expect(result.current.errorRecoveryAttempts).toBe(3);

    // Try one more time - should not increment
    act(() => {
      result.current.recoverFromError();
    });

    expect(result.current.errorRecoveryAttempts).toBe(3);
  });
});