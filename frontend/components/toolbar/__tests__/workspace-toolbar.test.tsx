/**
 * Workspace Toolbar Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests for toolbar component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkspaceToolbar } from '../workspace-toolbar';

describe('WorkspaceToolbar', () => {
  const mockProps = {
    onSearchClick: vi.fn(),
    onFilterToggle: vi.fn(),
    onGroupToggle: vi.fn(),
    onSortToggle: vi.fn(),
    onExport: vi.fn(),
    onRefresh: vi.fn(),
    onSettings: vi.fn(),
    transactionCount: 0,
    activeFilterCount: 0,
  };

  it('renders all action buttons', () => {
    render(<WorkspaceToolbar {...mockProps} />);
    expect(screen.getByLabelText(/Search/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Filter/)).toBeInTheDocument();
    expect(screen.getByLabelText(/group/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Sort/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Export/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Refresh/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Settings/)).toBeInTheDocument();
  });

  it('displays transaction count', () => {
    render(<WorkspaceToolbar {...mockProps} transactionCount={100} />);
    expect(screen.getByLabelText('100 transactions')).toBeInTheDocument();
  });

  it('shows filter count badge when filters active', () => {
    render(<WorkspaceToolbar {...mockProps} activeFilterCount={3} />);
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('does not show filter count badge when no filters', () => {
    render(<WorkspaceToolbar {...mockProps} activeFilterCount={0} />);
    // Check that no badge with the filter count is displayed
    const filterButton = screen.getByLabelText(/Filter/);
    expect(filterButton.querySelector('span[data-slot="badge"]')).not.toBeInTheDocument();
  });

  it('has toolbar role and aria-label', () => {
    render(<WorkspaceToolbar {...mockProps} />);
    expect(screen.getByRole('toolbar')).toBeInTheDocument();
  });

  it('calls onSearchClick when search button clicked', () => {
    render(<WorkspaceToolbar {...mockProps} />);
    screen.getByLabelText(/Search/).click();
    expect(mockProps.onSearchClick).toHaveBeenCalledTimes(1);
  });

  it('calls onFilterToggle when filter button clicked', () => {
    render(<WorkspaceToolbar {...mockProps} />);
    screen.getByLabelText(/Filter/).click();
    expect(mockProps.onFilterToggle).toHaveBeenCalledTimes(1);
  });

  it('calls onRefresh when refresh button clicked', () => {
    render(<WorkspaceToolbar {...mockProps} />);
    screen.getByLabelText(/Refresh/).click();
    expect(mockProps.onRefresh).toHaveBeenCalledTimes(1);
  });

  it('shows loading state on refresh button', () => {
    render(<WorkspaceToolbar {...mockProps} loading={true} />);
    const refreshButton = screen.getByLabelText(/Refresh/);
    expect(refreshButton).toBeDisabled();
  });

  // Error state tests
  it('shows error message when error is provided', () => {
    render(<WorkspaceToolbar {...mockProps} error="Failed to load transactions" />);
    expect(screen.getByText('Failed to load transactions')).toBeInTheDocument();
  });

  it('does not show error message when no error', () => {
    render(<WorkspaceToolbar {...mockProps} />);
    expect(screen.queryByText(/Failed to load/)).not.toBeInTheDocument();
  });

  // Customization tests
  it('hides search button when showSearch is false', () => {
    render(<WorkspaceToolbar {...mockProps} showSearch={false} />);
    expect(screen.queryByLabelText(/Search/)).not.toBeInTheDocument();
  });

  it('hides filter button when showFilter is false', () => {
    render(<WorkspaceToolbar {...mockProps} showFilter={false} />);
    expect(screen.queryByLabelText(/Filter/)).not.toBeInTheDocument();
  });

  it('hides group button when showGroup is false', () => {
    render(<WorkspaceToolbar {...mockProps} showGroup={false} />);
    expect(screen.queryByLabelText(/group/i)).not.toBeInTheDocument();
  });

  it('hides sort button when showSort is false', () => {
    render(<WorkspaceToolbar {...mockProps} showSort={false} />);
    expect(screen.queryByLabelText(/Sort/)).not.toBeInTheDocument();
  });

  it('hides export button when showExport is false', () => {
    render(<WorkspaceToolbar {...mockProps} showExport={false} />);
    expect(screen.queryByLabelText(/Export/)).not.toBeInTheDocument();
  });

  it('hides refresh button when showRefresh is false', () => {
    render(<WorkspaceToolbar {...mockProps} showRefresh={false} />);
    expect(screen.queryByLabelText(/Refresh/)).not.toBeInTheDocument();
  });

  it('hides settings button when showSettings is false', () => {
    render(<WorkspaceToolbar {...mockProps} showSettings={false} />);
    expect(screen.queryByLabelText(/Settings/)).not.toBeInTheDocument();
  });
});
