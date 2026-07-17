/**
 * Tests for EvidenceCard component
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EvidenceCard } from '@/components/explainability/components/EvidenceCard'

describe('EvidenceCard', () => {
  it('renders evidence description', () => {
    render(
      <EvidenceCard
        evidence={{
          id: 'e1',
          type: 'data',
          description: 'Account balance',
          value: 10000000,
        }}
      />,
    )
    expect(screen.getByText('Account balance')).toBeInTheDocument()
  })

  it('renders number value', () => {
    render(
      <EvidenceCard
        evidence={{
          id: 'e1',
          type: 'data',
          description: 'Balance',
          value: 10000000,
        }}
      />,
    )
    expect(screen.getByText('10,000,000')).toBeInTheDocument()
  })

  it('renders string value', () => {
    render(
      <EvidenceCard
        evidence={{
          id: 'e1',
          type: 'data',
          description: 'Type',
          value: 'checking',
        }}
      />,
    )
    expect(screen.getByText('checking')).toBeInTheDocument()
  })

  it('renders null value as em dash', () => {
    render(
      <EvidenceCard
        evidence={{
          id: 'e1',
          type: 'data',
          description: 'Optional',
          value: null,
        }}
      />,
    )
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders sourceId when present', () => {
    render(
      <EvidenceCard
        evidence={{
          id: 'e1',
          type: 'data',
          description: 'Balance',
          value: 10000000,
          sourceId: 'acc-1',
        }}
      />,
    )
    expect(screen.getByText('Source: acc-1')).toBeInTheDocument()
  })
})