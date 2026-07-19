/**
 * Pagination Controls Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests for pagination controls component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PaginationControls } from '../pagination-controls';

// Mock scrollIntoView for Radix UI Select
beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

describe('PaginationControls', () => {
  it('renders pagination controls with correct page info', () => {
    render(
      <PaginationControls
        page={1}
        limit={50}
        total={100}
        onPageChange={vi.fn()}
        onLimitChange={vi.fn()}
      />
    );
    expect(screen.getByText('1 / 2')).toBeInTheDocument();
    expect(screen.getByText('Showing 1 to 50 of 100 transactions')).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    render(
      <PaginationControls
        page={1}
        limit={50}
        total={100}
        onPageChange={vi.fn()}
        onLimitChange={vi.fn()}
      />
    );
    const buttons = screen.getAllByRole('button');
    // First button is "first page" - should be disabled
    expect(buttons[0]).toBeDisabled();
    // Second button is "previous page" - should be disabled
    expect(buttons[1]).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(
      <PaginationControls
        page={2}
        limit={50}
        total={100}
        onPageChange={vi.fn()}
        onLimitChange={vi.fn()}
      />
    );
    const buttons = screen.getAllByRole('button');
    // Last two buttons are "next page" and "last page" - should be disabled
    expect(buttons[buttons.length - 1]).toBeDisabled();
    expect(buttons[buttons.length - 2]).toBeDisabled();
  });

  it('calls onPageChange when next button is clicked', () => {
    const onPageChange = vi.fn();
    render(
      <PaginationControls
        page={1}
        limit={50}
        total={100}
        onPageChange={onPageChange}
        onLimitChange={vi.fn()}
      />
    );
    const buttons = screen.getAllByRole('button');
    // Third button is "next page"
    fireEvent.click(buttons[2]);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange when previous button is clicked', () => {
    const onPageChange = vi.fn();
    render(
      <PaginationControls
        page={2}
        limit={50}
        total={100}
        onPageChange={onPageChange}
        onLimitChange={vi.fn()}
      />
    );
    const buttons = screen.getAllByRole('button');
    // Second button is "previous page"
    fireEvent.click(buttons[1]);
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('calls onLimitChange when limit selector changes', () => {
    const onLimitChange = vi.fn();
    render(
      <PaginationControls
        page={1}
        limit={50}
        total={100}
        onPageChange={vi.fn()}
        onLimitChange={onLimitChange}
      />
    );
    // Find the select trigger and click it
    const selectTrigger = screen.getByRole('combobox');
    fireEvent.click(selectTrigger);
    // Select 100 from the dropdown
    const option = screen.getByText('100');
    fireEvent.click(option);
    expect(onLimitChange).toHaveBeenCalledWith(100);
  });

  it('returns null when total is 0', () => {
    const { container } = render(
      <PaginationControls
        page={1}
        limit={50}
        total={0}
        onPageChange={vi.fn()}
        onLimitChange={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('has proper aria-labels for accessibility', () => {
    render(
      <PaginationControls
        page={1}
        limit={50}
        total={100}
        onPageChange={vi.fn()}
        onLimitChange={vi.fn()}
      />
    );
    expect(screen.getByLabelText('Go to first page')).toBeInTheDocument();
    expect(screen.getByLabelText('Go to previous page')).toBeInTheDocument();
    expect(screen.getByLabelText('Go to next page')).toBeInTheDocument();
    expect(screen.getByLabelText('Go to last page')).toBeInTheDocument();
    expect(screen.getByLabelText('Select items per page')).toBeInTheDocument();
  });
});