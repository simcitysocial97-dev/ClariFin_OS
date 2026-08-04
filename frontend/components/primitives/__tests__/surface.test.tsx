/**
 * Surface Primitive Tests - Milestone 8 Visual Language
 *
 * Tests the foundational Surface primitive that everything is built on.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Surface } from '@/components/primitives/surface/surface';
import { surfaceVariants } from '@/components/primitives/surface/surface';

describe('Surface Primitive — Milestone 8', () => {
  describe('Rendering', () => {
    it('renders children', () => {
      render(<Surface>Test Content</Surface>);
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('applies fin-surface class by default', () => {
      const { container } = render(<Surface />);
      expect(container.firstChild).toHaveClass('fin-surface');
    });

    it('spreads additional props', () => {
      const { container } = render(<Surface data-testid="surface" />);
      expect(container.firstChild).toHaveAttribute('data-testid', 'surface');
    });
  });

  describe('Surface Variants', () => {
    it('default variant has no extra surface class', () => {
      const { container } = render(<Surface variant="default" />);
      expect(container.firstChild).toHaveClass('fin-surface');
    });

    it('raised variant applies fin-surface-raised', () => {
      const { container } = render(<Surface variant="raised" />);
      expect(container.firstChild).toHaveClass('fin-surface-raised');
    });

    it('interactive variant applies fin-surface-interactive', () => {
      const { container } = render(<Surface variant="interactive" />);
      expect(container.firstChild).toHaveClass('fin-surface-interactive');
    });

    it('selected variant applies fin-surface-selected', () => {
      const { container } = render(<Surface variant="selected" />);
      expect(container.firstChild).toHaveClass('fin-surface-selected');
    });

    it('floating variant applies fin-surface-floating', () => {
      const { container } = render(<Surface variant="floating" />);
      expect(container.firstChild).toHaveClass('fin-surface-floating');
    });

    it('overlay variant applies fin-surface-overlay', () => {
      const { container } = render(<Surface variant="overlay" />);
      expect(container.firstChild).toHaveClass('fin-surface-overlay');
    });

    it('graph variant applies fin-surface-graph', () => {
      const { container } = render(<Surface variant="graph" />);
      expect(container.firstChild).toHaveClass('fin-surface-graph');
    });
  });

  describe('Density', () => {
    it('default density applies p-3', () => {
      const { container } = render(<Surface density="default" />);
      expect(container.firstChild).toHaveClass('p-3');
    });

    it('comfortable density applies p-4', () => {
      const { container } = render(<Surface density="comfortable" />);
      expect(container.firstChild).toHaveClass('p-4');
    });

    it('compact density applies p-2', () => {
      const { container } = render(<Surface density="compact" />);
      expect(container.firstChild).toHaveClass('p-2');
    });

    it('spacious density applies p-6', () => {
      const { container } = render(<Surface density="spacious" />);
      expect(container.firstChild).toHaveClass('p-6');
    });

    it('terminal density applies p-1.5', () => {
      const { container } = render(<Surface density="terminal" />);
      expect(container.firstChild).toHaveClass('p-1.5');
    });

    it('none density applies p-0', () => {
      const { container } = render(<Surface density="none" />);
      expect(container.firstChild).toHaveClass('p-0');
    });
  });

  describe('Radius', () => {
    it('default radius is md', () => {
      const { container } = render(<Surface />);
      expect(container.firstChild).toHaveClass('rounded-[var(--radius-md)]');
    });

    it('sm radius applies correctly', () => {
      const { container } = render(<Surface radius="sm" />);
      expect(container.firstChild).toHaveClass('rounded-[var(--radius-sm)]');
    });

    it('lg radius applies correctly', () => {
      const { container } = render(<Surface radius="lg" />);
      expect(container.firstChild).toHaveClass('rounded-[var(--radius-lg)]');
    });

    it('none radius applies correctly', () => {
      const { container } = render(<Surface radius="none" />);
      expect(container.firstChild).toHaveClass('rounded-none');
    });
  });

  describe('Borderless', () => {
    it('borderless=false keeps border', () => {
      const { container } = render(<Surface borderless={false} />);
      expect(container.firstChild).not.toHaveClass('border-0');
    });

    it('borderless=true removes border', () => {
      const { container } = render(<Surface borderless={true} />);
      expect(container.firstChild).toHaveClass('border-0');
    });
  });

  describe('Data Attributes', () => {
    it('sets data-slot="surface"', () => {
      const { container } = render(<Surface />);
      expect(container.firstChild).toHaveAttribute('data-slot', 'surface');
    });

    it('sets data-variant attribute', () => {
      const { container } = render(<Surface variant="raised" />);
      expect(container.firstChild).toHaveAttribute('data-variant', 'raised');
    });

    it('sets data-density attribute', () => {
      const { container } = render(<Surface density="compact" />);
      expect(container.firstChild).toHaveAttribute('data-density', 'compact');
    });
  });

  describe('CVA Variants', () => {
    it('surfaceVariants is a function', () => {
      expect(typeof surfaceVariants).toBe('function');
    });

    it('surfaceVariants returns classes for default options', () => {
      expect(surfaceVariants({})).toContain('fin-surface');
    });

    it('surfaceVariants returns correct classes for interactive variant', () => {
      const classes = surfaceVariants({ variant: 'interactive' });
      expect(classes).toContain('fin-surface-interactive');
    });
  });
});
