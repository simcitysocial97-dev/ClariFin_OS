/**
 * Data Display Primitive Tests - Milestone 8 Visual Language
 *
 * Tests for MoneyValue, PercentageValue, DeltaValue, ConfidenceValue,
 * TimestampValue, and IdentifierValue primitives.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  MoneyValue,
  PercentageValue,
  DeltaValue,
  ConfidenceValue,
  TimestampValue,
  IdentifierValue,
} from '@/components/primitives/data-display';

describe('Data Display Primitives — Milestone 8', () => {
  describe('MoneyValue', () => {
    it('formats paise as INR', () => {
      render(<MoneyValue paise={50000} />);
      expect(screen.getByText(/₹500\.00/)).toBeInTheDocument();
    });

    it('formats zero correctly', () => {
      render(<MoneyValue paise={0} />);
      expect(screen.getByText('₹0.00')).toBeInTheDocument();
    });

    it('formats negative values with minus sign', () => {
      render(<MoneyValue paise={-2500} />);
      expect(screen.getByText('-₹25.00')).toBeInTheDocument();
    });

    it('formats large values with Indian locale grouping', () => {
      render(<MoneyValue paise={15000000} />);
      expect(screen.getByText(/₹1,50,000\.00/)).toBeInTheDocument();
    });

    it('applies fin-amount class for default variant', () => {
      const { container } = render(<MoneyValue paise={100} />);
      expect(container.firstChild).toHaveClass('fin-amount');
    });

    it('applies fin-amount-large class for large variant', () => {
      const { container } = render(<MoneyValue paise={100} variant="large" />);
      expect(container.firstChild).toHaveClass('fin-amount-large');
    });

    it('applies fin-amount-compact class for compact variant', () => {
      const { container } = render(<MoneyValue paise={100} variant="compact" />);
      expect(container.firstChild).toHaveClass('fin-amount-compact');
    });

    it('applies tabular-nums class', () => {
      const { container } = render(<MoneyValue paise={100} />);
      expect(container.firstChild).toHaveClass('tabular-nums');
    });

    describe('Sign options', () => {
      it('auto sign: negative shows minus', () => {
        render(<MoneyValue paise={-100} sign="auto" />);
        expect(screen.getByText('-₹1.00')).toBeInTheDocument();
      });

      it('auto sign: positive shows no sign', () => {
        render(<MoneyValue paise={100} sign="auto" />);
        expect(screen.getByText('₹1.00')).toBeInTheDocument();
      });

      it('positive sign: positive shows plus', () => {
        render(<MoneyValue paise={100} sign="positive" />);
        expect(screen.getByText('+₹1.00')).toBeInTheDocument();
      });

      it('negative sign: positive shows no sign', () => {
        render(<MoneyValue paise={100} sign="negative" />);
        expect(screen.getByText('₹1.00')).toBeInTheDocument();
      });

      it('always sign: positive shows plus', () => {
        render(<MoneyValue paise={100} sign="always" />);
        expect(screen.getByText('+₹1.00')).toBeInTheDocument();
      });

      it('always sign: negative shows minus', () => {
        render(<MoneyValue paise={-100} sign="always" />);
        expect(screen.getByText('-₹1.00')).toBeInTheDocument();
      });

      it('never sign: no sign shown', () => {
        render(<MoneyValue paise={-100} sign="never" />);
        expect(screen.getByText('₹1.00')).toBeInTheDocument();
      });

      it('never sign: positive shows no sign', () => {
        render(<MoneyValue paise={100} sign="never" />);
        expect(screen.getByText('₹1.00')).toBeInTheDocument();
      });
    });

    describe('Color', () => {
      it('positive value gets positive color class', () => {
        const { container } = render(<MoneyValue paise={100} sign="positive" />);
        expect(container.firstChild).toHaveClass('text-[var(--color-positive-600)]');
      });

      it('negative value gets negative color class', () => {
        const { container } = render(<MoneyValue paise={-100} />);
        expect(container.firstChild).toHaveClass('text-[var(--color-negative-600)]');
      });

      it('zero value gets no color class', () => {
        const { container } = render(<MoneyValue paise={0} />);
        expect(container.firstChild).not.toHaveClass('text-[var(--color-positive-600)]');
        expect(container.firstChild).not.toHaveClass('text-[var(--color-negative-600)]');
      });
    });
  });

  describe('PercentageValue', () => {
    it('formats value with % suffix', () => {
      render(<PercentageValue value={12.5} />);
      expect(screen.getByText('12.5%')).toBeInTheDocument();
    });

    it('formats negative values with minus', () => {
      render(<PercentageValue value={-5.25} />);
      expect(screen.getByText('-5.3%')).toBeInTheDocument();
    });

    it('formats zero correctly', () => {
      render(<PercentageValue value={0} />);
      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });

    it('custom decimals', () => {
      render(<PercentageValue value={12.345} decimals={2} />);
      expect(screen.getByText('12.35%')).toBeInTheDocument();
    });

    it('applies fin-percentage class', () => {
      const { container } = render(<PercentageValue value={10} />);
      expect(container.firstChild).toHaveClass('fin-percentage');
    });

    it('positive value gets positive color when colored', () => {
      const { container } = render(<PercentageValue value={5} />);
      expect(container.firstChild).toHaveClass('text-[var(--color-positive-600)]');
    });

    it('negative value gets negative color when colored', () => {
      const { container } = render(<PercentageValue value={-5} />);
      expect(container.firstChild).toHaveClass('text-[var(--color-negative-600)]');
    });

    it('zero value gets no color when colored', () => {
      const { container } = render(<PercentageValue value={0} />);
      expect(container.firstChild).not.toHaveClass('text-[var(--color-positive-600)]');
    });

    it('no color when colored=false', () => {
      const { container } = render(<PercentageValue value={-5} colored={false} />);
      expect(container.firstChild).not.toHaveClass('text-[var(--color-negative-600)]');
    });

    describe('Sign options', () => {
      it('positive sign shows plus for positive', () => {
        render(<PercentageValue value={5} sign="positive" />);
        expect(screen.getByText('+5.0%')).toBeInTheDocument();
      });

      it('always sign shows plus for positive', () => {
        render(<PercentageValue value={5} sign="always" />);
        expect(screen.getByText('+5.0%')).toBeInTheDocument();
      });

      it('auto sign shows no sign for positive', () => {
        render(<PercentageValue value={5} sign="auto" />);
        expect(screen.getByText('5.0%')).toBeInTheDocument();
      });

      it('never sign hides minus', () => {
        render(<PercentageValue value={-5} sign="never" />);
        expect(screen.getByText('5.0%')).toBeInTheDocument();
      });
    });
  });

  describe('DeltaValue', () => {
    it('renders positive value with arrow up', () => {
      const { container } = render(<DeltaValue value={5} />);
      expect(container).toHaveTextContent('+₹5');
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders negative value with arrow down', () => {
      const { container } = render(<DeltaValue value={-5} />);
      expect(container).toHaveTextContent('₹5');
      expect(container.querySelector('svg')).toBeInTheDocument();
      expect(container.firstChild).toHaveClass('text-[var(--color-negative-600)]');
    });

    it('renders zero value with minus', () => {
      render(<DeltaValue value={0} />);
      expect(screen.getByText('₹0')).toBeInTheDocument();
    });

    it('applies fin-amount-compact class', () => {
      const { container } = render(<DeltaValue value={5} />);
      expect(container.firstChild).toHaveClass('fin-amount-compact');
    });

    it('inline-flex layout', () => {
      const { container } = render(<DeltaValue value={5} />);
      expect(container.firstChild).toHaveClass('inline-flex');
    });

    it('positive color for positive value', () => {
      const { container } = render(<DeltaValue value={5} />);
      expect(container.firstChild).toHaveClass('text-[var(--color-positive-600)]');
    });

    it('negative color for negative value', () => {
      const { container } = render(<DeltaValue value={-5} />);
      expect(container.firstChild).toHaveClass('text-[var(--color-negative-600)]');
    });

    it('tertiary color for zero value', () => {
      const { container } = render(<DeltaValue value={0} />);
      expect(container.firstChild).toHaveClass('text-[var(--text-tertiary)]');
    });

    it('no color when colored=false', () => {
      const { container } = render(<DeltaValue value={-5} colored={false} />);
      expect(container.firstChild).not.toHaveClass('text-[var(--color-negative-600)]');
    });

    it('no arrow when showArrow=false', () => {
      const { container } = render(<DeltaValue value={5} showArrow={false} />);
      expect(container.querySelector('svg')).toBeNull();
    });

    it('renders percentage variant', () => {
      render(<DeltaValue value={5.5} variant="percentage" />);
      expect(screen.getByText('+5.5%')).toBeInTheDocument();
    });

    it('renders number variant', () => {
      render(<DeltaValue value={5.5} variant="number" />);
      expect(screen.getByText('+5.5')).toBeInTheDocument();
    });
  });

  describe('ConfidenceValue', () => {
    it('renders value with % suffix', () => {
      render(<ConfidenceValue value={85} />);
      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('applies fin-confidence class', () => {
      const { container } = render(<ConfidenceValue value={85} />);
      expect(container.firstChild).toHaveClass('fin-confidence');
    });

    it('renders High label for value >= 80', () => {
      render(<ConfidenceValue value={90} />);
      expect(screen.getByText('High')).toBeInTheDocument();
    });

    it('renders Medium label for 50 <= value < 80', () => {
      render(<ConfidenceValue value={65} />);
      expect(screen.getByText('Medium')).toBeInTheDocument();
    });

    it('renders Low label for value < 50', () => {
      render(<ConfidenceValue value={30} />);
      expect(screen.getByText('Low')).toBeInTheDocument();
    });

    it('high confidence gets confidence-high color', () => {
      const { container } = render(<ConfidenceValue value={85} showDot />);
      const dot = container.querySelector('.h-2.w-2');
      expect(dot).toHaveClass('bg-[var(--color-confidence-high)]');
    });

    it('medium confidence gets confidence-medium color', () => {
      const { container } = render(<ConfidenceValue value={60} showDot />);
      const dot = container.querySelector('.h-2.w-2');
      expect(dot).toHaveClass('bg-[var(--color-confidence-medium)]');
    });

    it('low confidence gets confidence-low color', () => {
      const { container } = render(<ConfidenceValue value={30} showDot />);
      const dot = container.querySelector('.h-2.w-2');
      expect(dot).toHaveClass('bg-[var(--color-confidence-low)]');
    });

    it('hides dot when showDot=false', () => {
      const { container } = render(<ConfidenceValue value={85} showDot={false} />);
      expect(container.querySelector('.h-2.w-2')).toBeNull();
    });

    it('hides label when showLabel=false', () => {
      render(<ConfidenceValue value={85} showLabel={false} />);
      expect(screen.queryByText('High')).not.toBeInTheDocument();
    });

    it('applies tabular-nums to value', () => {
      const { container } = render(<ConfidenceValue value={85} />);
      expect(container.querySelector('.tabular-nums')).toBeInTheDocument();
    });
  });

  describe('TimestampValue', () => {
    const testDate = '2025-06-15T10:30:00Z';

    it('renders as time element with dateTime', () => {
      const { container } = render(<TimestampValue value={testDate} />);
      const el = container.firstChild as HTMLElement;
      expect(el.tagName).toBe('TIME');
      expect(el).toHaveAttribute('dateTime', testDate);
    });

    it('applies fin-timestamp class', () => {
      const { container } = render(<TimestampValue value={testDate} />);
      expect(container.firstChild).toHaveClass('fin-timestamp');
    });

    it('formats date by default', () => {
      render(<TimestampValue value={testDate} />);
      expect(screen.getByText(/15 Jun 2025/)).toBeInTheDocument();
    });

    it('formats datetime', () => {
      render(<TimestampValue value={testDate} format="datetime" />);
      expect(screen.getByText(/15 Jun 2025/)).toBeInTheDocument();
    });

    it('formats compact', () => {
      render(<TimestampValue value={testDate} format="compact" />);
      const text = screen.getByText(/15\/06\/25/);
      expect(text).toBeInTheDocument();
    });

    it('formats month-year', () => {
      render(<TimestampValue value={testDate} format="month-year" />);
      expect(screen.getByText(/Jun 2025/)).toBeInTheDocument();
    });

    it('renders relative format (just now)', () => {
      const now = new Date().toISOString();
      render(<TimestampValue value={now} format="relative" />);
      expect(screen.getByText('just now')).toBeInTheDocument();
    });

    it('renders relative format (5m ago)', () => {
      const past = new Date(Date.now() - 5 * 60000).toISOString();
      render(<TimestampValue value={past} format="relative" />);
      expect(screen.getByText('5m ago')).toBeInTheDocument();
    });

    it('returns fallback for invalid date', () => {
      render(<TimestampValue value="invalid-date" />);
      expect(screen.getByText('invalid-date')).toBeInTheDocument();
    });
  });

  describe('IdentifierValue', () => {
    it('renders full value by default', () => {
      render(<IdentifierValue value="TXN123456789" />);
      expect(screen.getByText('TXN123456789')).toBeInTheDocument();
    });

    it('applies fin-identifier class', () => {
      const { container } = render(<IdentifierValue value="ID123" />);
      expect(container.firstChild).toHaveClass('fin-identifier');
    });

    it('short variant truncates to 8 chars', () => {
      render(<IdentifierValue value="ABCDEFGHIJ" variant="short" />);
      expect(screen.getByText('ABCDEFGH')).toBeInTheDocument();
    });

    it('truncated variant truncates long values', () => {
      render(<IdentifierValue value="ABCDEFGHIJKLMNOP" variant="truncated" maxLength={10} />);
      const text = screen.getByText(/A.*P/);
      expect(text.textContent).toContain('...');
    });

    it('full variant shows complete value', () => {
      render(<IdentifierValue value="SHORT" variant="full" />);
      expect(screen.getByText('SHORT')).toBeInTheDocument();
    });

    it('renders prefix', () => {
      render(<IdentifierValue value="12345" prefix="TXN-" />);
      expect(screen.getByText('TXN-12345')).toBeInTheDocument();
    });

    it('copyable renders with cursor-pointer', () => {
      const { container } = render(<IdentifierValue value="ID123" copyable />);
      expect(container.firstChild).toHaveClass('cursor-pointer');
    });

    it('copyable renders hover text-link class', () => {
      const { container } = render(<IdentifierValue value="ID123" copyable />);
      expect(container.firstChild).toHaveClass('hover:text-[var(--text-link)]');
    });

    it('copyable sets title attribute', () => {
      const { container } = render(<IdentifierValue value="ID123" copyable />);
      expect(container.firstChild).toHaveAttribute('title', 'Copy: ID123');
    });

    it('non-copyable does not set title to copy', () => {
      const { container } = render(<IdentifierValue value="ID123" />);
      expect(container.firstChild).toHaveAttribute('title', 'ID123');
    });

    it('clicking copyable copies to clipboard', () => {
      const writeText = vi.fn();
      Object.assign(navigator, {
        clipboard: { writeText },
      });
      render(<IdentifierValue value="ID123" copyable />);
      fireEvent.click(screen.getByText('ID123'));
      expect(writeText).toHaveBeenCalledWith('ID123');
    });
  });
});
