/**
 * Card Primitive Tests - Milestone 8 Visual Language
 *
 * Tests the Card primitive: rendering, slots, variants, density,
 * and integration with the Surface primitive.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardBody, CardFooter, cardVariants } from '@/components/primitives/card/card';

describe('Card Primitive — Milestone 8', () => {
  describe('Rendering', () => {
    it('renders children', () => {
      render(<Card>Card Content</Card>);
      expect(screen.getByText('Card Content')).toBeInTheDocument();
    });

    it('applies fin-surface class by default', () => {
      const { container } = render(<Card />);
      expect(container.firstChild).toHaveClass('fin-surface');
    });

    it('sets data-slot="surface"', () => {
      const { container } = render(<Card />);
      expect(container.firstChild).toHaveAttribute('data-slot', 'surface');
    });
  });

  describe('Variants', () => {
    it('default variant renders without error', () => {
      const { container } = render(<Card variant="default" />);
      expect(container.firstChild).toHaveClass('fin-surface');
    });

    it('elevated variant applies raised surface', () => {
      const { container } = render(<Card variant="elevated" />);
      expect(container.firstChild).toHaveClass('fin-surface-raised');
    });

    it('interactive variant applies interactive surface', () => {
      const { container } = render(<Card variant="interactive" />);
      expect(container.firstChild).toHaveClass('fin-surface-interactive');
    });

    it('selected variant applies selected surface', () => {
      const { container } = render(<Card variant="selected" />);
      expect(container.firstChild).toHaveClass('fin-surface-selected');
    });
  });

  describe('Density', () => {
    it('compact density applies p-2', () => {
      const { container } = render(<Card density="compact" />);
      expect(container.firstChild).toHaveClass('p-2');
    });

    it('default density applies p-3', () => {
      const { container } = render(<Card density="default" />);
      expect(container.firstChild).toHaveClass('p-3');
    });

    it('comfortable density applies p-4', () => {
      const { container } = render(<Card density="comfortable" />);
      expect(container.firstChild).toHaveClass('p-4');
    });

    it('spacious density applies p-6', () => {
      const { container } = render(<Card density="spacious" />);
      expect(container.firstChild).toHaveClass('p-6');
    });
  });

  describe('Radius', () => {
    it('default radius is md', () => {
      const { container } = render(<Card />);
      expect(container.firstChild).toHaveClass('rounded-[var(--radius-md)]');
    });

    it('lg radius applies correctly', () => {
      const { container } = render(<Card radius="lg" />);
      expect(container.firstChild).toHaveClass('rounded-[var(--radius-lg)]');
    });
  });

  describe('CardHeader', () => {
    it('renders title', () => {
      render(<CardHeader title="My Card" />);
      expect(screen.getByText('My Card')).toBeInTheDocument();
    });

    it('renders subtitle', () => {
      render(<CardHeader title="Title" subtitle="Subtitle" />);
      expect(screen.getByText('Subtitle')).toBeInTheDocument();
    });

    it('renders actions', () => {
      render(<CardHeader title="Title" actions={<button>Action</button>} />);
      expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
    });

    it('renders children', () => {
      render(<CardHeader>Custom Content</CardHeader>);
      expect(screen.getByText('Custom Content')).toBeInTheDocument();
    });

    it('applies border-b', () => {
      const { container } = render(<CardHeader title="Title" />);
      expect(container.firstChild).toHaveClass('border-b');
    });

    it('uses fin-panel-header for title text', () => {
      const { container } = render(<CardHeader title="Title" />);
      expect(container.querySelector('.fin-panel-header')).toBeInTheDocument();
    });
  });

  describe('CardBody', () => {
    it('renders children', () => {
      render(<CardBody>Body Content</CardBody>);
      expect(screen.getByText('Body Content')).toBeInTheDocument();
    });

    it('applies flex-1 by default', () => {
      const { container } = render(<CardBody>Body</CardBody>);
      expect(container.firstChild).toHaveClass('flex-1');
    });

    it('applies overflow-y-auto when scrollable', () => {
      const { container } = render(<CardBody scrollable>Body</CardBody>);
      expect(container.firstChild).toHaveClass('overflow-y-auto');
    });
  });

  describe('CardFooter', () => {
    it('renders children', () => {
      render(<CardFooter>Footer Content</CardFooter>);
      expect(screen.getByText('Footer Content')).toBeInTheDocument();
    });

    it('applies border-t by default', () => {
      const { container } = render(<CardFooter>Footer</CardFooter>);
      expect(container.firstChild).toHaveClass('border-t');
    });

    it('removes border when divided=false', () => {
      const { container } = render(<CardFooter divided={false}>Footer</CardFooter>);
      expect(container.firstChild).not.toHaveClass('border-t');
    });
  });

  describe('CVA Variants', () => {
    it('cardVariants returns classes for default options', () => {
      expect(cardVariants({})).toContain('fin-surface');
    });

    it('cardVariants returns correct classes for elevated', () => {
      expect(cardVariants({ variant: 'elevated' })).toContain('fin-surface-raised');
    });
  });
});
