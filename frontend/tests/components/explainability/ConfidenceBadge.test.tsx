/**
 * Tests for ConfidenceBadge component
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConfidenceBadge } from '@/components/explainability/components/ConfidenceBadge'

describe('ConfidenceBadge', () => {
  it('renders confidence percentage', () => {
    render(<ConfidenceBadge value={8500} />)
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('renders with reason as title', () => {
    render(<ConfidenceBadge value={7500} reason="High confidence from data" />)
    const badge = screen.getByTitle('High confidence from data')
    expect(badge).toBeInTheDocument()
  })

  it('has correct aria-label', () => {
    render(<ConfidenceBadge value={5000} />)
    const badge = screen.getByLabelText('Confidence: 50%')
    expect(badge).toBeInTheDocument()
  })
})