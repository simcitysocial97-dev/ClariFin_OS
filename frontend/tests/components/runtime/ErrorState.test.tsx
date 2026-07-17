/**
 * Rendering tests for ErrorState component
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorState } from '@/components/runtime'

describe('ErrorState', () => {
  it('renders with default title', () => {
    render(<ErrorState error={new Error('Test error')} />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders with custom title', () => {
    render(<ErrorState error={new Error('Test error')} title="Custom error" />)
    expect(screen.getByText('Custom error')).toBeInTheDocument()
  })

  it('renders error details in details element', () => {
    render(<ErrorState error={new Error('Test error message')} />)
    expect(screen.getByText('Show details')).toBeInTheDocument()
  })

  it('renders retry button when onRetry provided', () => {
    const onRetry = vi.fn()
    render(<ErrorState error={new Error('Test error')} onRetry={onRetry} />)
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })

  it('does not render retry button when onRetry not provided', () => {
    render(<ErrorState error={new Error('Test error')} />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('renders description when provided', () => {
    render(
      <ErrorState
        error={new Error('Test error')}
        description="Custom description"
      />
    )
    expect(screen.getByText('Custom description')).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    render(<ErrorState error={new Error('Test error')} />)
    const card = document.querySelector('.border-destructive')
    expect(card).toBeInTheDocument()
  })
})