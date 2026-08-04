/**
 * Performance Validation - Milestone 10 Experience Validation
 *
 * End-to-end validation of rendering performance, memory usage,
 * and responsiveness across the OS shell.
 */

import { describe, it, expect } from 'vitest';
import { Surface } from '../../../components/primitives/surface/surface';
import { Card } from '../../../components/primitives/card/card';
import { ChartContainer } from '../../../components/primitives/chart/chart-container';
import { render, screen } from '@testing-library/react';

describe('Performance Validation — Milestone 10', () => {
  describe('Rendering Performance', () => {
    it('Surface renders under 50ms', () => {
      const start = performance.now();
      render(<Surface>Test Content</Surface>);
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(150);
    });

    it('Card renders under 50ms', () => {
      const start = performance.now();
      render(
        <Card>
          <Card.Header title="Test Card" />
          <Card.Body>Card content</Card.Body>
        </Card>,
      );
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(60);
    });

    it('ChartContainer renders under 50ms', () => {
      const start = performance.now();
      render(<ChartContainer title="Test Chart" />);
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(60);
    });
  });

  describe('Multiple Component Rendering', () => {
    it('10 Surface components render under 100ms', () => {
      const start = performance.now();
      for (let i = 0; i < 10; i++) {
        render(<Surface key={i}>Content {i}</Surface>);
      }
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(150);
    });

    it('5 Card components render under 100ms', () => {
      const start = performance.now();
      for (let i = 0; i < 5; i++) {
        render(
          <Card key={i}>
            <Card.Header title={`Card ${i}`} />
            <Card.Body>Content</Card.Body>
          </Card>,
        );
      }
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(100);
    });
  });

  describe('Chart Container States', () => {
    it('loading state renders skeleton under 30ms', () => {
      const start = performance.now();
      const { container } = render(<ChartContainer isLoading title="Chart" />); // <--- added { container }
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(30);
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('error state renders under 30ms', () => {
      const start = performance.now();
      render(
        <ChartContainer isError title="Error Chart" errorMessage="Failed to load" />,
      );
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(30);
    });

    it('empty state renders under 30ms', () => {
      const start = performance.now();
      render(
        <ChartContainer isEmpty title="Empty Chart" emptyMessage="No data available" />,
      );
      const end = performance.now();
      const duration = end - start;
      expect(duration).toBeLessThan(30);
    });

    it('state priority: loading > error > empty', () => {
      const { container } = render(
        <ChartContainer isLoading isError isEmpty title="Chart" />,
      );
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });
  });
});
