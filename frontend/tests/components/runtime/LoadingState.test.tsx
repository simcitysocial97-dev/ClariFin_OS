/**
 * Rendering tests for LoadingState component
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingState } from '@/components/runtime'

describe('LoadingState', () => {
  it('renders spinner variant by default', () => {
    render(<LoadingState />)
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders spinner variant with custom message', () => {
    render(<LoadingState variant="spinner" message="Fetching data..." />)
    expect(screen.getByText('Fetching data...')).toBeInTheDocument()
  })

  it('renders inline variant', () => {
    render(<LoadingState variant="inline" message="Processing..." />)
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('Processing...')).toBeInTheDocument()
  })

  it('renders compact variant', () => {
    render(<LoadingState variant="compact" />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders fullscreen variant', () => {
    render(<LoadingState variant="fullscreen" message="Please wait..." />)
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('Please wait...')).toBeInTheDocument()
  })

  it('renders skeleton variant with default rows', () => {
    render(<LoadingState variant="skeleton" />)
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBe(3)
  })

  it('renders skeleton variant with custom rows', () => {
    render(<LoadingState variant="skeleton" rows={5} />)
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBe(5)
  })

  it('applies custom className', () => {
    render(<LoadingState className="custom-class" />)
    const status = screen.getByRole('status')
    expect(status.className).toContain('custom-class')
  })
})