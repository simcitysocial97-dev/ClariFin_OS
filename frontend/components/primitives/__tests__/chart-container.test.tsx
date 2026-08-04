/**
 * Chart Container Primitive Tests - Milestone 8 Visual Language
 *
 * Tests loading, error, empty, and default states of ChartContainer.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChartContainer } from '@/components/primitives/chart/chart-container';

describe('ChartContainer Primitive — Milestone 8', () => {
  describe('Default State', () => {
    it('renders children', () => {
      render(<ChartContainer>Chart Content</ChartContainer>);
      expect(screen.getByText('Chart Content')).toBeInTheDocument();
    });

    it('renders title when provided', () => {
      render(<ChartContainer title="My Chart">Content</ChartContainer>);
      expect(screen.getByText('My Chart')).toBeInTheDocument();
    });

    it('does not render title section when not provided', () => {
      const { container } = render(<ChartContainer>Content</ChartContainer>);
      expect(container.querySelector('.fin-section-header')).toBeNull();
    });

    it('applies fin-surface and fin-surface-raised', () => {
      const { container } = render(<ChartContainer>Content</ChartContainer>);
      expect(container.firstChild).toHaveClass('fin-surface');
      expect(container.firstChild).toHaveClass('fin-surface-raised');
    });
  });

  describe('Loading State', () => {
    it('renders loading skeleton', () => {
      const { container } = render(<ChartContainer isLoading>Content</ChartContainer>);
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('does not render children when loading', () => {
      render(<ChartContainer isLoading>Chart Content</ChartContainer>);
      expect(screen.queryByText('Chart Content')).not.toBeInTheDocument();
    });

    it('renders two skeleton lines', () => {
      const { container } = render(<ChartContainer isLoading />);
      const skeletons = container.querySelectorAll('.animate-pulse .h-4, .animate-pulse .h-32');
      expect(skeletons.length).toBe(2);
    });
  });

  describe('Error State', () => {
    it('renders default error message', () => {
      render(<ChartContainer isError />);
      expect(screen.getByText('Unable to load chart data')).toBeInTheDocument();
    });

    it('renders custom error message', () => {
      render(<ChartContainer isError errorMessage="Custom error" />);
      expect(screen.getByText('Custom error')).toBeInTheDocument();
    });

    it('applies fin-error class', () => {
      const { container } = render(<ChartContainer isError />);
      expect(container.firstChild).toHaveClass('fin-error');
    });

    it('renders retry button when onRetry provided', () => {
      const onRetry = vi.fn();
      render(<ChartContainer isError onRetry={onRetry} />);
      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    });

    it('does not render retry button when onRetry not provided', () => {
      render(<ChartContainer isError />);
      expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument();
    });

    it('calls onRetry when retry button clicked', () => {
      const onRetry = vi.fn();
      render(<ChartContainer isError onRetry={onRetry} />);
      fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
      expect(onRetry).toHaveBeenCalled();
    });

    it('does not render children when error', () => {
      render(<ChartContainer isError>Chart Content</ChartContainer>);
      expect(screen.queryByText('Chart Content')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('renders default empty message', () => {
      render(<ChartContainer isEmpty />);
      expect(screen.getByText('No data available')).toBeInTheDocument();
    });

    it('renders custom empty message', () => {
      render(<ChartContainer isEmpty emptyMessage="No charts to show" />);
      expect(screen.getByText('No charts to show')).toBeInTheDocument();
    });

    it('renders search icon', () => {
      const { container } = render(<ChartContainer isEmpty />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('does not render children when empty', () => {
      render(<ChartContainer isEmpty>Chart Content</ChartContainer>);
      expect(screen.queryByText('Chart Content')).not.toBeInTheDocument();
    });
  });

  describe('Density', () => {
    it('default density applies p-3', () => {
      const { container } = render(<ChartContainer>Content</ChartContainer>);
      expect(container.firstChild).toHaveClass('p-3');
    });

    it('compact density applies p-2', () => {
      const { container } = render(<ChartContainer density="compact">Content</ChartContainer>);
      expect(container.firstChild).toHaveClass('p-2');
    });

    it('comfortable density applies p-4', () => {
      const { container } = render(<ChartContainer density="comfortable">Content</ChartContainer>);
      expect(container.firstChild).toHaveClass('p-4');
    });

    it('spacious density applies p-6', () => {
      const { container } = render(<ChartContainer density="spacious">Content</ChartContainer>);
      expect(container.firstChild).toHaveClass('p-6');
    });

    it('terminal density applies p-1.5', () => {
      const { container } = render(<ChartContainer density="terminal">Content</ChartContainer>);
      expect(container.firstChild).toHaveClass('p-1.5');
    });
  });

  describe('Priority States', () => {
    it('isLoading takes priority over isError and isEmpty', () => {
      const { container } = render(<ChartContainer isLoading isError isEmpty />);
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('isError takes priority over isEmpty', () => {
      render(<ChartContainer isError isEmpty errorMessage="Error" emptyMessage="Empty" />);
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.queryByText('Empty')).not.toBeInTheDocument();
    });
  });
});
