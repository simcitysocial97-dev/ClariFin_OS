/**
 * Error Message Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests for error message component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorMessage } from '../error-message';

describe('ErrorMessage', () => {
  it('renders with default title', () => {
    render(<ErrorMessage message="Something went wrong" />);
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(<ErrorMessage title="Custom Error" message="Something went wrong" />);
    expect(screen.getByText('Custom Error')).toBeInTheDocument();
  });

  it('renders error message', () => {
    render(<ErrorMessage message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders retry button when onRetry provided', () => {
    render(<ErrorMessage message="Error" onRetry={() => {}} />);
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('does not render retry button when onRetry not provided', () => {
    render(<ErrorMessage message="Error" />);
    expect(screen.queryByText('Retry')).not.toBeInTheDocument();
  });

  it('calls onRetry when retry button clicked', () => {
    const onRetry = vi.fn();
    render(<ErrorMessage message="Error" onRetry={onRetry} />);
    screen.getByText('Retry').click();
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('has alert role for accessibility', () => {
    render(<ErrorMessage message="Error" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});