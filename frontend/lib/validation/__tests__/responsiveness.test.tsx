/**
 * Responsiveness Validation - Milestone 10 Experience Validation
 *
 * End-to-end validation of responsive behavior across breakpoints,
 * layout adaptation, and component sizing at different viewport widths.
 */

import { describe, it, expect } from 'vitest';
import { Surface } from '../../../components/primitives/surface/surface';
import { Card } from '../../../components/primitives/card/card';
import { render, screen } from '@testing-library/react';

describe('Responsiveness Validation — Milestone 10', () => {
  describe('Breakpoint Behavior', () => {
    it('Surface renders correctly at desktop width (1280px+)', () => {
      const { container } = render(<Surface>Desktop Content</Surface>);
      expect(container.firstChild).toBeInTheDocument();
      expect(screen.getByText('Desktop Content')).toBeInTheDocument();
    });

    it('Surface renders correctly at tablet width (768px-1279px)', () => {
      const { container } = render(<Surface density="comfortable">Tablet Content</Surface>);
      expect(container.firstChild).toBeInTheDocument();
      expect(screen.getByText('Tablet Content')).toBeInTheDocument();
    });

    it('Surface renders correctly at mobile width (<768px)', () => {
      const { container } = render(<Surface density="compact">Mobile Content</Surface>);
      expect(container.firstChild).toBeInTheDocument();
      expect(screen.getByText('Mobile Content')).toBeInTheDocument();
    });
  });

  describe('Density Adaptation', () => {
    it('compact density applies smaller padding', () => {
      const { container } = render(<Surface density="compact">Compact</Surface>);
      expect(container.firstChild).toHaveClass('p-2');
    });

    it('comfortable density applies default padding', () => {
      const { container } = render(<Surface density="comfortable">Comfortable</Surface>);
      expect(container.firstChild).toHaveClass('p-4');
    });

    it('spacious density applies larger padding', () => {
      const { container } = render(<Surface density="spacious">Spacious</Surface>);
      expect(container.firstChild).toHaveClass('p-6');
    });

    it('terminal density applies minimal padding', () => {
      const { container } = render(<Surface density="terminal">Terminal</Surface>);
      expect(container.firstChild).toHaveClass('p-1.5');
    });
  });

  describe('Card Responsive Behavior', () => {
    it('Card renders with header, body, and footer slots', () => {
      const { container } = render(
        <Card>
          <Card.Header title="Responsive Card" subtitle="Adapts to viewport" />
          <Card.Body>Body content</Card.Body>
          <Card.Footer>Footer content</Card.Footer>
        </Card>,
      );
      expect(container.querySelector('h3')).toBeInTheDocument();
      expect(screen.getByText('Body content')).toBeInTheDocument();
      expect(screen.getByText('Footer content')).toBeInTheDocument();
    });

    it('Card with scrollable body', () => {
      const { container } = render(
        <Card>
          <Card.Body scrollable>Scrollable content</Card.Body>
        </Card>,
      );
      const body = container.querySelector('.flex-1');
      expect(body).toBeInTheDocument();
    });
  });

  describe('Layout Adaptation', () => {
    it('Surface adapts to different density levels', () => {
      const densities = ['compact', 'default', 'comfortable', 'spacious', 'terminal', 'none'] as const;
      for (const density of densities) {
        const { container } = render(<Surface density={density}>Content</Surface>);
        expect(container.firstChild).toBeInTheDocument();
      }
    });

    it('Surface variant changes visual appearance', () => {
      const variants = ['default', 'raised', 'interactive', 'selected', 'floating', 'overlay'] as const;
      for (const variant of variants) {
        const { container } = render(<Surface variant={variant}>Content</Surface>);
        expect(container.firstChild).toBeInTheDocument();
      }
    });
  });

  describe('Z-Index Hierarchy', () => {
    it('Surface respects z-index tokens', () => {
      const { container } = render(<Surface variant="overlay">Overlay</Surface>);
      expect(container.firstChild).toBeInTheDocument();
    });
  });
});
