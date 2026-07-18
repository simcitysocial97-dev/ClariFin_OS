/**
 * Tests for ExplainabilityProvider
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ExplainabilityProvider, useExplainabilityContext } from '@/components/explainability/providers/ExplainabilityProvider'

// Mock the store
vi.mock('@/lib/store/explainability-store', () => ({
  useExplainabilityStore: vi.fn(),
}))

const mockExplanation = {
  metric: 'test',
  value: 100,
  confidence: { value: 5000, reason: 'Test confidence' },
  evidence: [],
  sources: [],
  calculationSteps: [],
}

function TestComponent() {
  const { showExplanation, close } = useExplainabilityContext()
  return (
    <div>
      <button onClick={() => showExplanation(mockExplanation)}>Show</button>
      <button onClick={close}>Close</button>
    </div>
  )
}

describe('ExplainabilityProvider', () => {
  it('provides showExplanation and close functions', () => {
    vi.mocked(require('@/lib/store/explainability-store').useExplainabilityStore).mockReturnValue({
      setExplanation: vi.fn(),
      setRecommendation: vi.fn(),
      reset: vi.fn(),
    })

    render(
      <ExplainabilityProvider>
        <TestComponent />
      </ExplainabilityProvider>,
    )

    expect(screen.getByText('Show')).toBeInTheDocument()
    expect(screen.getByText('Close')).toBeInTheDocument()
  })
})