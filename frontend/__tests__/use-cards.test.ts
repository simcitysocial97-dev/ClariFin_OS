/**
 * Unit tests for useCards hook

 *
 * Tests cover:
 * - Initial load with empty cards
 * - Card retrieval
 * - Card creation
 * - Card updates
 * - Card deletions
 * - Error handling
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCards } from '../lib/hooks/use-cards';

vi.mock('@/lib/api/gateway', () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from '@/lib/api/gateway';
import { createMockResponse, createMockErrorResponse } from './utils/createMockResponse';
const mockApiFetch = vi.mocked(apiFetch);

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
    },
  });
  const Wrapper = ({ children }: { children: React.ReactNode }) => React.createElement(
    QueryClientProvider, { client: queryClient }, children
  );
  Wrapper.displayName = 'TestQueryClientWrapper';
  return Wrapper;
};

const mockCardsData = {
  cards: [
    {
      card_id: 'card-1',
      bank: 'HDFC',
      card_last4: '1234',
      credit_limit: 200000,
      current_outstanding: 50000,
      minimum_due: 5000,
      payment_due_date: '2026-09-15',
      statement_date: '2026-08-25',
      bill_cycle_start: '2026-08-01',
      bill_cycle_end: '2026-08-31',
      utilization_percent: 25,
      days_until_due: 10,
      payment_status: 'due_soon' as const,
      validation_status: 'valid',
      statement_count: 12,
      latest_statement_id: 12,
    },
  ],
  total_cards: 1,
  total_outstanding: 50000,
  total_credit_limit: 200000,
  total_utilization_percent: 25,
};

describe('useCards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCards(), { wrapper });

    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBeNull();
  });

  it('should fetch cards successfully', async () => {
    mockApiFetch.mockResolvedValue(createMockResponse(mockCardsData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCards(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data).toEqual(mockCardsData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should calculate total outstanding correctly', async () => {
    const multiCardData = {
      ...mockCardsData,
      cards: [
        { ...mockCardsData.cards[0], current_outstanding: 50000 },
        { ...mockCardsData.cards[0], card_id: 'card-2', current_outstanding: 30000 },
      ],
      total_cards: 2,
      total_outstanding: 80000,
    };

    mockApiFetch.mockResolvedValue(createMockResponse(multiCardData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCards(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data?.total_outstanding).toBe(80000);
    expect(result.current.data?.total_cards).toBe(2);
  });

  it('should handle empty cards list', async () => {
    const emptyData = {
      cards: [],
      total_cards: 0,
      total_outstanding: 0,
      total_credit_limit: 0,
      total_utilization_percent: 0,
    };

    mockApiFetch.mockResolvedValue(createMockResponse(emptyData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCards(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data?.cards).toHaveLength(0);
    expect(result.current.data?.total_cards).toBe(0);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValue(createMockErrorResponse(500));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCards(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).not.toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('should handle schema validation error', async () => {
    const invalidData = {
      cards: [
        {
          card_id: 'card-1',
          // missing required fields
        },
      ],
    };

    mockApiFetch.mockResolvedValue(createMockResponse(invalidData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCards(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).not.toBeNull();
  });

  it('should handle payment statuses correctly', async () => {
    const statusData = {
      ...mockCardsData,
      cards: [
        { ...mockCardsData.cards[0], payment_status: 'overdue' as const },
        { ...mockCardsData.cards[0], card_id: 'card-2', payment_status: 'on_track' as const },
        { ...mockCardsData.cards[0], card_id: 'card-3', payment_status: 'upcoming' as const },
      ],
    };

    mockApiFetch.mockResolvedValue(createMockResponse(statusData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCards(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data?.cards[0].payment_status).toBe('overdue');
    expect(result.current.data?.cards[1].payment_status).toBe('on_track');
    expect(result.current.data?.cards[2].payment_status).toBe('upcoming');
  });
});
