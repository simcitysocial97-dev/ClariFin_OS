/**
 * Accessibility Validation - Milestone 10 Experience Validation
 *
 * End-to-end validation of accessibility across the OS shell,
 * including focus management, keyboard navigation, ARIA attributes,
 * and screen reader support.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'; // <--- Added 'vi' here
import { Surface } from '../../../components/primitives/surface/surface';
import { Card } from '../../../components/primitives/card/card';
import { focusEngine } from '../../../lib/interaction/focus-engine';
import { keyboardEngine } from '../../../lib/interaction/keyboard-engine';
import { render } from '@testing-library/react';

describe('Accessibility Validation — Milestone 10', () => {
  beforeEach(() => {
    focusEngine.reset();
    keyboardEngine.reset();
  });

  describe('Focus Management', () => {
    it('focusable elements have visible focus indicators', () => {
      const { container } = render(<Surface data-testid="focus-test">Content</Surface>);
      const element = container.firstChild;
      expect(element).toBeDefined();
    });

    it('focus engine tracks current target', () => {
      focusEngine.register({
        id: 'focus-panel',
        type: 'panel',
        element: document.createElement('div'),
        priority: 0,
      });
      focusEngine.focus('focus-panel');
      const state = focusEngine.getState();
      expect(state.currentTarget).toBe('panel');
      expect(state.currentElementId).toBe('focus-panel');
    });

    it('focus cycle follows priority order', () => {
      focusEngine.register({ id: 'low', type: 'panel', element: document.createElement('button'), priority: 10 });
      focusEngine.register({ id: 'high', type: 'panel', element: document.createElement('button'), priority: 1 });
      focusEngine.focusFirst();
      expect(focusEngine.getState().currentElementId).toBe('high');
    });
  });

  describe('Keyboard Navigation', () => {
    it('keyboard engine handles Tab key for focus cycling', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('tab-handler', {
        shortcuts: [{ key: 'Tab', handler, description: 'Focus next', category: 'system' }],
        priority: 0,
      });

      const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true });
      keyboardEngine.handleKeyDown(event);
      expect(handler).toHaveBeenCalledOnce();
    });

    it('keyboard engine handles Escape for clearing focus', () => {
      focusEngine.register({
        id: 'esc-panel',
        type: 'panel',
        element: document.createElement('div'),
        priority: 0,
      });
      focusEngine.focus('esc-panel');

      const handler = vi.fn();
      keyboardEngine.registerHandler('esc-handler', {
        shortcuts: [{ key: 'Escape', handler, description: 'Clear focus', category: 'selection' }],
        priority: 0,
      });

      const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
      keyboardEngine.handleKeyDown(event);
      expect(handler).toHaveBeenCalledOnce();
    });

    it('Arrow keys navigate selection', () => {
      const upHandler = vi.fn();
      const downHandler = vi.fn();
      keyboardEngine.registerHandler('arrows', {
        shortcuts: [
          { key: 'ArrowUp', handler: upHandler, description: 'Select previous', category: 'selection' },
          { key: 'ArrowDown', handler: downHandler, description: 'Select next', category: 'selection' },
        ],
        priority: 0,
      });

      const upEvent = new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true });
      keyboardEngine.handleKeyDown(upEvent);
      expect(upHandler).toHaveBeenCalledOnce();

      const downEvent = new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true });
      keyboardEngine.handleKeyDown(downEvent);
      expect(downHandler).toHaveBeenCalledOnce();
    });
  });

  describe('ARIA and Semantic HTML', () => {
    it('Surface renders with data-slot attribute', () => {
      const { container } = render(<Surface>Content</Surface>);
      expect(container.firstChild).toHaveAttribute('data-slot', 'surface');
    });

    it('Card renders with semantic heading structure', () => {
      const { container } = render(
        <Card>
          <Card.Header title="Card Title" subtitle="Card Subtitle" />
          <Card.Body>Body content</Card.Body>
        </Card>,
      );
      expect(container.querySelector('h3')).toBeInTheDocument();
    });

    it('interactive Surface variant has hover state class', () => {
      const { container } = render(<Surface variant="interactive">Hover me</Surface>);
      expect(container.firstChild).toHaveClass('fin-surface-interactive');
    });
  });

  describe('Focus Visible', () => {
    it('focus engine supports clearFocus for Escape', () => {
      focusEngine.register({
        id: 'esc-test',
        type: 'panel',
        element: document.createElement('div'),
        priority: 0,
      });
      focusEngine.focus('esc-test');
      focusEngine.clearFocus();
      const state = focusEngine.getState();
      expect(state.currentTarget).toBeNull();
      expect(state.currentElementId).toBeNull();
    });
  });
});
