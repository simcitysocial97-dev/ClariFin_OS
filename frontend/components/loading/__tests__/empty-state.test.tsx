/**
 * Empty State Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests for empty state component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EmptyState } from '../empty-state';

describe('EmptyState', () => {
  it('renders with default title', () => {
    render(<EmptyState />);
    expect(screen.getByText('No transactions found')).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(<EmptyState title="No results" />);
    expect(screen.getByText('No results')).toBeInTheDocument();
  });

  it('renders with default description', () => {
    render(<EmptyState />);
    expect(screen.getByText('Try adjusting your filters or search query.')).toBeInTheDocument();
  });

  it('renders with custom description', () => {
    render(<EmptyState description="No data available" />);
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('renders clear filters button when onAction provided', () => {
    render(<EmptyState onAction={() => {}} />);
    expect(screen.getByText('Clear filters')).toBeInTheDocument();
  });

  it('does not render action button when onAction not provided', () => {
    render(<EmptyState />);
    expect(screen.queryByText('Clear filters')).not.toBeInTheDocument();
  });

  it('calls onAction when action button clicked', () => {
    const onAction = vi.fn();
    render(<EmptyState onAction={onAction} />);
    screen.getByText('Clear filters').click();
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('renders with custom action label', () => {
    render(<EmptyState actionLabel="Try again" onAction={() => {}} />);
    expect(screen.getByText('Try again')).toBeInTheDocument();
  });
});