/**
 * Graph Invocation Tests - Stage 7 Graph Runtime Integration
 *
 * Tests for GraphInvocation public API: invoke, close, subscribe, isOpen,
 * getScope, getResult, and getRuntime.
 *
 * Note: Event bus integration (selection sync, workspace sync, keyboard)
 * is tested indirectly through the component tests.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { graphInvocation, resetGraphInvocation, type GraphScope } from '../graph-invocation';
import { runtimeEventBus } from '@/lib/event-bus';
import { overlayStore } from '@/components/os-shell/overlay-layer';
import { financialGraphRuntime } from '../runtime';

// ===== Mocks =====
vi.mock('@/components/os-shell/overlay-layer', () => ({
  overlayStore: {
    request: vi.fn(),
    getOverlays: vi.fn(() => []),
    dismiss: vi.fn(),
  },
}));

vi.mock('@/lib/graph/runtime', () => ({
  financialGraphRuntime: {
    related: vi.fn().mockReturnValue({ nodes: [], edges: [], metadata: {} }),
    build: vi.fn().mockReturnValue({ nodes: [], edges: [], metadata: {} }),
    select: vi.fn(),
    focus: vi.fn(),
  },
}));

vi.mock('@/lib/event-bus', () => ({
  runtimeEventBus: {
    publish: vi.fn(),
    subscribe: vi.fn(),
  },
  GRAPH_OVERLAY_OPENED: 'GraphOverlayOpened',
  GRAPH_OVERLAY_CLOSED: 'GraphOverlayClosed',
  SELECTION_CHANGED: 'SelectionChanged',
  SELECTION_CLEARED: 'SelectionCleared',
}));

// ===== Helpers =====
function createScope(overrides: Partial<GraphScope> = {}): GraphScope {
  return {
    trigger: 'command',
    mode: 'overlay',
    focusDepth: 2,
    ...overrides,
  };
}

// ===== Tests =====
describe('GraphInvocation — Milestone 7', () => {
  beforeEach(() => {
    resetGraphInvocation();
    vi.clearAllMocks();
  });

  describe('invoke()', () => {
    it('sets active scope', () => {
      const scope = createScope();
      graphInvocation.invoke(scope);
      expect(graphInvocation.getScope()).toEqual(scope);
    });

    it('opens overlay request for overlay mode', () => {
      const scope = createScope({ mode: 'overlay' });
      graphInvocation.invoke(scope);

      expect(overlayStore.request).toHaveBeenCalledOnce();
      const req = (overlayStore.request as ReturnType<typeof vi.fn>).mock.calls[0][0];
      expect(req.type).toBe('graph-exploration');
      expect(req.dismissible).toBe(true);
    });

    it('does not open overlay for context-panel mode', () => {
      const scope = createScope({ mode: 'context-panel', entityId: 'test:123' });
      graphInvocation.invoke(scope);

      expect(overlayStore.request).not.toHaveBeenCalled();
    });

    it('publishes GRAPH_OVERLAY_OPENED event for overlay mode', () => {
      graphInvocation.invoke(createScope({ mode: 'overlay' }));

      expect(runtimeEventBus.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'GraphOverlayOpened',
          source: 'GraphRuntime',
        }),
      );
    });

    it('calls financialGraphRuntime.related for entity-based invocation', () => {
      const scope = createScope({ mode: 'overlay', trigger: 'selection', entityId: 'tx:abc' });
      graphInvocation.invoke(scope);

      expect(financialGraphRuntime.related).toHaveBeenCalledWith('tx:abc', 2);
    });
  });

  describe('close()', () => {
    it('clears active scope', () => {
      graphInvocation.invoke(createScope());
      expect(graphInvocation.isOpen()).toBe(true);

      graphInvocation.close('user-dismissed');
      expect(graphInvocation.getScope()).toBeNull();
      expect(graphInvocation.getResult()).toBeNull();
    });

    it('dismisses graph exploration overlays from store', () => {
      (overlayStore.getOverlays as ReturnType<typeof vi.fn>).mockReturnValue([
        { id: 'graph-1', type: 'graph-exploration' },
        { id: 'cmd-1', type: 'command-palette' },
      ]);

      graphInvocation.close('test');

      expect(overlayStore.dismiss).toHaveBeenCalledWith('graph-1');
      expect(overlayStore.dismiss).not.toHaveBeenCalledWith('cmd-1');
    });

    it('publishes GRAPH_OVERLAY_CLOSED event with reason', () => {
      graphInvocation.close('workspace-switched');

      expect(runtimeEventBus.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'GraphOverlayClosed',
          payload: { reason: 'workspace-switched' },
        }),
      );
    });
  });

  describe('isOpen()', () => {
    it('returns false when no scope is active', () => {
      expect(graphInvocation.isOpen()).toBe(false);
    });

    it('returns true after invoke', () => {
      graphInvocation.invoke(createScope());
      expect(graphInvocation.isOpen()).toBe(true);
    });

    it('returns false after close', () => {
      graphInvocation.invoke(createScope());
      graphInvocation.close();
      expect(graphInvocation.isOpen()).toBe(false);
    });
  });

  describe('subscribe()', () => {
    it('notifies subscribers on state change', () => {
      const listener = vi.fn();
      graphInvocation.subscribe(listener);

      graphInvocation.invoke(createScope());
      expect(listener).toHaveBeenCalledOnce();
    });

    it('unsubscribe removes listener', () => {
      const listener = vi.fn();
      const unsub = graphInvocation.subscribe(listener);

      unsub();
      graphInvocation.invoke(createScope());
      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('getRuntime()', () => {
    it('returns the FinancialGraphRuntime instance', () => {
      const runtime = graphInvocation.getRuntime();
      expect(runtime).toBe(financialGraphRuntime);
    });
  });

  describe('Invariant: Never replaces workspace', () => {
    it('always uses valid modes (overlay or context-panel)', () => {
      const validModes: GraphScope['mode'][] = ['overlay', 'context-panel'];

      for (const mode of validModes) {
        graphInvocation.invoke(createScope({ mode }));
        expect(graphInvocation.isOpen()).toBe(true);
        graphInvocation.close();
      }
    });
  });
});
