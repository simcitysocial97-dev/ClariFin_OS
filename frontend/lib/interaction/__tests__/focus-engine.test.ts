/**
 * Focus Engine Tests - Milestone 9 Interaction Polish
 *
 * Tests for focusable element registration, focus management,
 * tab cycling, and subscription behavior.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { focusEngine, registerFocusable, unregisterFocusable } from '../focus-engine';
import type { FocusableElement } from '../focus-engine';

function makeElement(id: string, type: FocusableElement['type'], priority = 0): FocusableElement {
  const el = {
    id,
    focus: vi.fn(),
    blur: vi.fn(),
  } as unknown as HTMLElement;
  return { id, type, element: el, priority };
}

describe('FocusEngine — Milestone 9', () => {
  beforeEach(() => {
    focusEngine.reset();
  });

  describe('Registration', () => {
    it('registers a focusable element', () => {
      focusEngine.register(makeElement('test-1', 'panel'));
      expect(focusEngine.getAll().length).toBe(1);
    });

    it('registers multiple elements', () => {
      focusEngine.register(makeElement('t1', 'panel'));
      focusEngine.register(makeElement('t2', 'table'));
      focusEngine.register(makeElement('t3', 'graph'));
      expect(focusEngine.getAll().length).toBe(3);
    });

    it('unregisters an element by ID', () => {
      focusEngine.register(makeElement('t1', 'panel'));
      expect(focusEngine.unregister('t1')).toBe(true);
      expect(focusEngine.getAll().length).toBe(0);
    });

    it('returns false when unregistering non-existent ID', () => {
      expect(focusEngine.unregister('nonexistent')).toBe(false);
    });

    it('overwrites existing element on re-register', () => {
      focusEngine.register(makeElement('t1', 'panel', 0));
      focusEngine.register(makeElement('t1', 'table', 5));
      const el = focusEngine.get('t1');
      expect(el?.type).toBe('table');
      expect(el?.priority).toBe(5);
    });

    it('gets element by ID', () => {
      const element = makeElement('test-get', 'panel');
      focusEngine.register(element);
      expect(focusEngine.get('test-get')).toEqual(element);
    });

    it('returns undefined for missing ID', () => {
      expect(focusEngine.get('missing')).toBeUndefined();
    });

    it('gets elements by type', () => {
      focusEngine.register(makeElement('t1', 'panel'));
      focusEngine.register(makeElement('t2', 'table'));
      focusEngine.register(makeElement('t3', 'panel'));
      const panels = focusEngine.getByType('panel');
      expect(panels.length).toBe(2);
    });
  });

  describe('Focus Management', () => {
    it('focuses an element by ID', () => {
      const element = makeElement('focus-test', 'panel');
      focusEngine.register(element);
      focusEngine.focus('focus-test');
      const state = focusEngine.getState();
      expect(state.currentTarget).toBe('panel');
      expect(state.currentElementId).toBe('focus-test');
    });

    it('does not throw for unknown element ID', () => {
      expect(() => focusEngine.focus('unknown')).not.toThrow();
    });
  });

  describe('Tab Cycling', () => {
    beforeEach(() => {
      focusEngine.register(makeElement('el-1', 'panel', 1));
      focusEngine.register(makeElement('el-2', 'table', 2));
      focusEngine.register(makeElement('el-3', 'graph', 3));
    });

    it('cycles to next element on focusNext', () => {
      focusEngine.focus('el-1');
      focusEngine.focusNext();
      expect(focusEngine.getState().currentElementId).toBe('el-2');
    });

    it('wraps around to first on focusNext when at last', () => {
      focusEngine.focusNext();
      focusEngine.focusNext();
      expect(focusEngine.getState().currentElementId).toBe('el-3');
      focusEngine.focusNext();
      expect(focusEngine.getState().currentElementId).toBe('el-1');
    });

    it('cycles to previous element on focusPrevious', () => {
      focusEngine.focusNext();
      focusEngine.focusPrevious();
      expect(focusEngine.getState().currentElementId).toBe('el-1');
    });

    it('wraps around to last on focusPrevious when at first', () => {
      focusEngine.focus('el-1');
      focusEngine.focusPrevious();
      expect(focusEngine.getState().currentElementId).toBe('el-3');
    });

    it('focusFirst focuses the first element', () => {
      focusEngine.focusFirst();
      expect(focusEngine.getState().currentElementId).toBe('el-1');
    });

    it('focusLast focuses the last element', () => {
      focusEngine.focusLast();
      expect(focusEngine.getState().currentElementId).toBe('el-3');
    });
  });

  describe('Target-Specific Focus', () => {
    const mockEl = { id: 'mock', focus: vi.fn() } as unknown as HTMLElement;

    it('focusPanel targets panel:{id}', () => {
      focusEngine.register({
        id: 'panel:my-panel',
        type: 'panel',
        element: mockEl,
        priority: 0,
      });
      focusEngine.focusPanel('my-panel');
      expect(focusEngine.getState().currentElementId).toBe('panel:my-panel');
      expect(focusEngine.getState().currentTarget).toBe('panel');
    });

    it('focusWidget targets widget:{id}', () => {
      focusEngine.register({
        id: 'widget:my-widget',
        type: 'widget',
        element: mockEl,
        priority: 0,
      });
      focusEngine.focusWidget('my-widget');
      expect(focusEngine.getState().currentElementId).toBe('widget:my-widget');
    });

    it('focusGraph targets graph:canvas', () => {
      focusEngine.register({
        id: 'graph:canvas',
        type: 'graph',
        element: mockEl,
        priority: 0,
      });
      focusEngine.focusGraph();
      expect(focusEngine.getState().currentElementId).toBe('graph:canvas');
    });

    it('focusTable targets table:{id}', () => {
      focusEngine.register({
        id: 'table:my-table',
        type: 'table',
        element: mockEl,
        priority: 0,
      });
      focusEngine.focusTable('my-table');
      expect(focusEngine.getState().currentElementId).toBe('table:my-table');
    });

    it('focusTimeline targets timeline:container', () => {
      focusEngine.register({
        id: 'timeline:container',
        type: 'timeline',
        element: mockEl,
        priority: 0,
      });
      focusEngine.focusTimeline();
      expect(focusEngine.getState().currentElementId).toBe('timeline:container');
    });

    it('focusInspector targets inspector:container', () => {
      focusEngine.register({
        id: 'inspector:container',
        type: 'inspector',
        element: mockEl,
        priority: 0,
      });
      focusEngine.focusInspector();
      expect(focusEngine.getState().currentElementId).toBe('inspector:container');
    });

    it('focusSearch targets search:input', () => {
      focusEngine.register({
        id: 'search:input',
        type: 'search',
        element: mockEl,
        priority: 0,
      });
      focusEngine.focusSearch();
      expect(focusEngine.getState().currentElementId).toBe('search:input');
    });
  });

  describe('Clear Focus', () => {
    it('clears focus state on clearFocus', () => {
      focusEngine.register(makeElement('t1', 'panel'));
      focusEngine.focus('t1');
      focusEngine.clearFocus();
      const state = focusEngine.getState();
      expect(state.currentTarget).toBeNull();
      expect(state.currentElementId).toBeNull();
      expect(state.cycleIndex).toBe(0);
    });
  });

  describe('Subscription', () => {
    it('subscribes to state changes', () => {
      const listener = vi.fn();
      focusEngine.subscribe(listener);
      focusEngine.register(makeElement('el-1', 'panel'));
      focusEngine.focus('el-1');
      expect(listener).toHaveBeenCalled();
    });

    it('unsubscribe stops receiving events', () => {
      const listener = vi.fn();
      const unsubscribe = focusEngine.subscribe(listener);
      unsubscribe();
      focusEngine.register(makeElement('el-1', 'panel'));
      focusEngine.focus('el-1');
      expect(listener).not.toHaveBeenCalled();
    });

    it('notifies listeners on clearFocus', () => {
      const listener = vi.fn();
      focusEngine.subscribe(listener);
      focusEngine.register(makeElement('el-1', 'panel'));
      focusEngine.focus('el-1');
      listener.mockClear();
      focusEngine.clearFocus();
      expect(listener).toHaveBeenCalled();
    });
  });

  describe('Reset', () => {
    it('clears all elements and state', () => {
      focusEngine.register(makeElement('t1', 'panel'));
      focusEngine.focus('t1');
      focusEngine.reset();
      expect(focusEngine.getAll().length).toBe(0);
      const state = focusEngine.getState();
      expect(state.currentTarget).toBeNull();
      expect(state.currentElementId).toBeNull();
    });
  });

  describe('Convenience Functions', () => {
    it('registerFocusable registers via convenience function', () => {
      const el = { id: 'conv-1', focus: vi.fn() } as unknown as HTMLElement;
      registerFocusable('conv-1', 'panel', el, 0);
      expect(focusEngine.get('conv-1')).toBeDefined();
    });

    it('unregisterFocusable removes via convenience function', () => {
      const el = { id: 'conv-2', focus: vi.fn() } as unknown as HTMLElement;
      registerFocusable('conv-2', 'panel', el, 0);
      expect(focusEngine.get('conv-2')).toBeDefined();
      unregisterFocusable('conv-2');
      expect(focusEngine.get('conv-2')).toBeUndefined();
    });
  });
});
