/**
 * Keyboard Engine Tests - Milestone 9 Interaction Polish
 *
 * Tests for shortcut matching, priority ordering,
 * component-scoped handlers, and enable/disable behavior.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { keyboardEngine, type ComponentKeyboardHandler } from '../keyboard-engine';
import type { KeyboardShortcut, KeyboardHandler } from '../interaction-types';

if (typeof document === 'undefined') {
  (globalThis as Record<string, unknown>).document = {
    activeElement: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
  (globalThis as Record<string, unknown>).HTMLInputElement = class HTMLInputElement {};
  (globalThis as Record<string, unknown>).HTMLTextAreaElement = class HTMLTextAreaElement {};
  (globalThis as Record<string, unknown>).navigator = { platform: 'Win32' };
}

function makeShortcut(
  key: string,
  overrides: Partial<KeyboardShortcut> = {},
): KeyboardShortcut {
  return {
    key,
    handler: vi.fn(),
    description: 'test',
    category: 'system',
    ...overrides,
  };
}

function makeEvent(key: string, modifiers: Record<string, boolean> = {}): KeyboardEvent {
  return {
    key,
    ctrlKey: modifiers.ctrl ?? false,
    metaKey: modifiers.meta ?? false,
    altKey: modifiers.alt ?? false,
    shiftKey: modifiers.shift ?? false,
    target: null,
    bubbles: true,
    preventDefault: vi.fn(),
    stopPropagation: vi.fn(),
  } as unknown as KeyboardEvent;
}

describe('KeyboardEngine — Milestone 9', () => {
  beforeEach(() => {
    keyboardEngine.reset();
  });

  describe('Handler Registration', () => {
    it('registers a handler', () => {
      const handler: KeyboardHandler = { shortcuts: [], priority: 0 };
      keyboardEngine.registerHandler('test-id', handler);
      expect(keyboardEngine.getState().enabled).toBe(true);
    });

    it('unregisters a handler', () => {
      const handler: KeyboardHandler = {
        shortcuts: [makeShortcut('a')],
        priority: 0,
      };
      keyboardEngine.registerHandler('test-id', handler);
      expect(keyboardEngine.unregisterHandler('test-id')).toBe(true);
      expect(keyboardEngine.unregisterHandler('test-id')).toBe(false);
    });

    it('overwrites existing handler on re-register', () => {
      const h1: KeyboardHandler = { shortcuts: [makeShortcut('a')], priority: 0 };
      const h2: KeyboardHandler = { shortcuts: [makeShortcut('b')], priority: 1 };
      keyboardEngine.registerHandler('id', h1);
      keyboardEngine.registerHandler('id', h2);
      const handler = keyboardEngine['handlers'].get('id');
      expect(handler?.shortcuts[0].key).toBe('b');
    });
  });

  describe('Component Handler Registration', () => {
    it('registers a component handler', () => {
      const handler: ComponentKeyboardHandler = {
        id: 'comp-1',
        shortcuts: [makeShortcut('a')],
      };
      keyboardEngine.registerComponentHandler(handler);
      expect(keyboardEngine.unregisterComponentHandler('comp-1')).toBe(true);
    });

    it('unregisters a component handler', () => {
      const handler: ComponentKeyboardHandler = {
        id: 'comp-1',
        shortcuts: [],
      };
      keyboardEngine.registerComponentHandler(handler);
      expect(keyboardEngine.unregisterComponentHandler('comp-1')).toBe(true);
      expect(keyboardEngine.unregisterComponentHandler('comp-1')).toBe(false);
    });

    it('uses default priority of 0', () => {
      const handler: ComponentKeyboardHandler = {
        id: 'comp-priority',
        shortcuts: [],
      };
      keyboardEngine.registerComponentHandler(handler);
      const stored = keyboardEngine['componentHandlers'].get('comp-priority');
      expect(stored?.priority).toBe(0);
    });
  });

  describe('Shortcut Matching', () => {
    it('matches a basic keypress', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('h1', {
        shortcuts: [{ key: 'a', handler, description: '', category: 'system' }],
        priority: 0,
      });
      const event = makeEvent('a');
      keyboardEngine.handleKeyDown(event);
      expect(handler).toHaveBeenCalledOnce();
    });

    it('matches Ctrl+K (command palette)', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('palette', {
        shortcuts: [{ key: 'k', ctrl: true, handler, description: '', category: 'system' }],
        priority: 0,
      });
      const event = makeEvent('k', { ctrl: true });
      keyboardEngine.handleKeyDown(event);
      expect(handler).toHaveBeenCalledOnce();
    });

    it('does not match when modifier is missing', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('h1', {
        shortcuts: [{ key: 'k', ctrl: true, handler, description: '', category: 'system' }],
        priority: 0,
      });
      const event = makeEvent('k');
      keyboardEngine.handleKeyDown(event);
      expect(handler).not.toHaveBeenCalled();
    });

    it('matches with Shift modifier', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('h1', {
        shortcuts: [{ key: 'k', shift: true, handler, description: '', category: 'system' }],
        priority: 0,
      });
      const event = makeEvent('k', { shift: true });
      keyboardEngine.handleKeyDown(event);
      expect(handler).toHaveBeenCalledOnce();
    });

    it('matches with Alt modifier', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('h1', {
        shortcuts: [{ key: 'ArrowLeft', alt: true, handler, description: '', category: 'system' }],
        priority: 0,
      });
      const event = makeEvent('ArrowLeft', { alt: true });
      keyboardEngine.handleKeyDown(event);
      expect(handler).toHaveBeenCalledOnce();
    });
  });

  describe('Priority Ordering', () => {
    it('higher priority handler is checked first', () => {
      const h1 = vi.fn();
      const h2 = vi.fn();
      keyboardEngine.registerHandler('low', {
        shortcuts: [{ key: 'a', handler: h1, description: '', category: 'system' }],
        priority: 0,
      });
      keyboardEngine.registerHandler('high', {
        shortcuts: [{ key: 'a', handler: h2, description: '', category: 'system' }],
        priority: 10,
      });
      const event = makeEvent('a');
      keyboardEngine.handleKeyDown(event);
      expect(h2).toHaveBeenCalledOnce();
      expect(h1).not.toHaveBeenCalled();
    });

    it('stops at first matching handler', () => {
      const h1 = vi.fn();
      const h2 = vi.fn();
      keyboardEngine.registerHandler('first', {
        shortcuts: [{ key: 'a', handler: h1, description: '', category: 'system' }],
        priority: 0,
      });
      keyboardEngine.registerHandler('second', {
        shortcuts: [{ key: 'b', handler: h2, description: '', category: 'system' }],
        priority: 0,
      });
      const event = makeEvent('a');
      keyboardEngine.handleKeyDown(event);
      expect(h1).toHaveBeenCalledOnce();
      expect(h2).not.toHaveBeenCalled();
    });
  });

  describe('Enable/Disable', () => {
    it('disables all keyboard handling', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('h1', {
        shortcuts: [{ key: 'a', handler, description: '', category: 'system' }],
        priority: 0,
      });
      keyboardEngine.disable();
      const event = makeEvent('a');
      keyboardEngine.handleKeyDown(event);
      expect(handler).not.toHaveBeenCalled();
    });

    it('re-enables keyboard handling', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('h1', {
        shortcuts: [{ key: 'a', handler, description: '', category: 'system' }],
        priority: 0,
      });
      keyboardEngine.disable();
      keyboardEngine.enable();
      const event = makeEvent('a');
      keyboardEngine.handleKeyDown(event);
      expect(handler).toHaveBeenCalledOnce();
    });

    it('reports enabled state correctly', () => {
      expect(keyboardEngine.isEnabled()).toBe(true);
      keyboardEngine.disable();
      expect(keyboardEngine.isEnabled()).toBe(false);
      keyboardEngine.enable();
      expect(keyboardEngine.isEnabled()).toBe(true);
    });
  });

  describe('Reset', () => {
    it('clears all handlers and state', () => {
      const handler = vi.fn();
      keyboardEngine.registerHandler('h1', {
        shortcuts: [{ key: 'a', handler, description: '', category: 'system' }],
        priority: 0,
      });
      keyboardEngine.reset();
      const event = makeEvent('a');
      keyboardEngine.handleKeyDown(event);
      expect(handler).not.toHaveBeenCalled();
    });
  });
});
