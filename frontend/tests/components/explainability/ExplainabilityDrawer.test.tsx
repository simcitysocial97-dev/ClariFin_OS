/**
 * Tests for ExplainabilityDrawer component
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ExplainabilityDrawer } from '@/components/explainability/ExplainabilityDrawer'
import { useExplainabilityStore } from '@/lib/store/explainability-store'

// Mock the store
vi.mock('@/lib/store/explainability-store', () => ({
  useExplainabilityStore: vi.fn(),
}))

const mockExplanation = {
  metric: 'netWorth',
  value: 12500000,
  confidence: { value: 8500, reason: 'High confidence from 3 accounts' },
  evidence: [
    { id: 'e1', type: 'data' as const, description: 'Account balance', value: 10000000 },
  ],
  sources: [
    { type: 'account', id: 'acc-1', name: 'Savings Account' },
  ],
  calculationSteps: [
    {
      stepId: 'step-1',
      description: 'Sum account balances',
      operation: 'ADD' as const,
      inputIds: ['acc-1', 'acc-2'],
      outputId: 'netWorth',
      order: 1,
    },
  ],
}

describe('ExplainabilityDrawer', () => {
  it('renders nothing when no explanation is selected', () => {
    vi.mocked(useExplainabilityStore).mockReturnValue({
      selectedExplanation: null,
      selectedRecommendation: null,
      activeTab: 'overview',
      expandedSteps: new Set(),
      searchQuery: '',
      setExplanation: vi.fn(),
      setRecommendation: vi.fn(),
      setActiveTab: vi.fn(),
      toggleStep: vi.fn(),
      setSearchQuery: vi.fn(),
      reset: vi.fn(),
    })

    const { container } = render(<ExplainabilityDrawer />)
    expect(container.firstChild).toBeNull()
  })

  it('renders with explanation data', () => {
    vi.mocked(useExplainabilityStore).mockReturnValue({
      selectedExplanation: mockExplanation,
      selectedRecommendation: null,
      activeTab: 'overview',
      expandedSteps: new Set(),
      searchQuery: '',
      setExplanation: vi.fn(),
      setRecommendation: vi.fn(),
      setActiveTab: vi.fn(),
      toggleStep: vi.fn(),
      setSearchQuery: vi.fn(),
      reset: vi.fn(),
    })

    render(<ExplainabilityDrawer />)

    expect(screen.getByText('netWorth')).toBeInTheDocument()
    expect(screen.getByText('Explanation and evidence for this metric')).toBeInTheDocument()
  })
})