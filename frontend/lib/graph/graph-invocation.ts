/**
 * Graph Invocation Layer - Stage 7 Graph Runtime Integration
 *
 * Connects SelectionRuntime, TimelineRuntime, WorkspaceRuntime, and CommandRuntime
 * to the FinancialGraphRuntime as an investigative overlay — never the primary surface.
 *
 * Architecture: SelectionRuntime / CommandRuntime → GraphInvocation → FinancialGraphRuntime → OverlayLayer
 *
 * Graph invariants:
 * - Investigative only. Never replaces the workspace surface.
 * - State is ephemeral (not persisted across sessions).
 * - Selection is delegated to SelectionRuntime, not managed here.
 * - Closes automatically when workspace switches.
 */

import type { GraphResult } from './types';
import { financialGraphRuntime } from './runtime';
import { overlayStore, type OverlayType } from '@/components/os-shell/overlay-layer';
import { runtimeEventBus, GRAPH_OVERLAY_OPENED, GRAPH_OVERLAY_CLOSED, SELECTION_CHANGED, SELECTION_CLEARED } from '../event-bus';

// ===== Graph Invocation Scope =====
export type GraphTrigger = 'selection' | 'command' | 'insight' | 'workspace-action';
export type GraphDisplayMode = 'context-panel' | 'overlay';

export interface GraphScope {
  trigger: GraphTrigger;
  entityId?: string;
  entityType?: string;
  mode: GraphDisplayMode;
  maxNodes?: number; // cap for context-panel mode
  focusDepth?: number;
}

// ===== Ephemeral State (module-level, not persisted) =====
let _activeScope: GraphScope | null = null;
let _graphResult: GraphResult | null = null;
const _listeners = new Set<(scope: GraphScope | null, result: GraphResult | null) => void>();

function notify() {
  _listeners.forEach(fn => fn(_activeScope, _graphResult));
}

// ===== Sync helpers =====
async function _buildContextPanel(scope: GraphScope) {
  if (!scope.entityId) return;
  try {
    const result = await financialGraphRuntime.related(scope.entityId, scope.focusDepth ?? 1);
    // Cap nodes for context-panel mode
    if (scope.maxNodes && result.nodes.length > scope.maxNodes) {
      const nodeSet = new Set<string>(result.nodes.slice(0, scope.maxNodes).map(n => n.id));
      result.nodes = result.nodes.filter(n => nodeSet.has(n.id));
      result.edges = result.edges.filter(e => nodeSet.has(e.source) && nodeSet.has(e.target));
    }
    _graphResult = result;
    notify();
  } catch {
    _graphResult = null;
    notify();
  }
}

async function _buildFullOverlay(scope: GraphScope) {
  try {
    let result: GraphResult;
    if (scope.entityId) {
      result = await financialGraphRuntime.related(scope.entityId, scope.focusDepth ?? 2);
    } else {
      result = await financialGraphRuntime.build();
    }
    _graphResult = result;
    notify();
  } catch {
    _graphResult = null;
    notify();
  }
}

// ===== Public API =====
export const graphInvocation = {
  /**
   * Invoke the graph from a trigger source.
   * Opens either context-panel or full overlay depending on mode.
   */
  invoke(scope: GraphScope): void {
    _activeScope = scope;
    if (scope.mode === 'context-panel') {
      _buildContextPanel(scope).catch(() => { /* ignore build errors */ });
    } else {
      _buildFullOverlay(scope).catch(() => { /* ignore build errors */ });
    }
    // Register overlay if opening full overlay
    if (scope.mode === 'overlay') {
      const id = `graph-${Date.now()}`;
      overlayStore.request({
        id,
        type: 'graph-exploration' as OverlayType,
        priority: 1001,
        dismissible: true,
        props: { scope, initialResult: _graphResult },
      });
      runtimeEventBus.publish({
        type: GRAPH_OVERLAY_OPENED,
        timestamp: Date.now(),
        source: 'GraphRuntime',
        payload: { scope, layout: 'force-directed' },
      });
    }
    notify();
  },

  /**
   * Close the graph overlay and clear state.
   * Dismisses any open overlay requests.
   */
  close(reason?: string): void {
    const prevScope = _activeScope;
    _activeScope = null;
    _graphResult = null;
    // Dismiss all graph exploration overlays
    overlayStore.getOverlays()
      .filter(o => o.type === 'graph-exploration')
      .forEach(o => overlayStore.dismiss(o.id));
    notify();
    runtimeEventBus.publish({
      type: GRAPH_OVERLAY_CLOSED,
      timestamp: Date.now(),
      source: 'GraphRuntime',
      payload: { reason: reason ?? 'unknown' },
    });

    const event = new CustomEvent('os-graph-closed', { detail: { reason, prevScope } });
    window.dispatchEvent(event);
  },

  /**
   * Get the current active scope.
   */
  getScope(): GraphScope | null {
    return _activeScope;
  },

  /**
   * Get the current graph result.
   */
  getResult(): GraphResult | null {
    return _graphResult;
  },

  /**
   * Check if the graph is currently open (any mode).
   */
  isOpen(): boolean {
    return _activeScope !== null;
  },

  /**
   * Subscribe to graph invocation state changes.
   */
  subscribe(fn: (scope: GraphScope | null, result: GraphResult | null) => void): () => void {
    _listeners.add(fn);
    return () => { _listeners.delete(fn); };
  },

  /**
   * Get the underlying FinancialGraphRuntime for direct access.
   */
  getRuntime() {
    return financialGraphRuntime;
  },
};

// ===== Runtime Integration — SelectionSync =====
// Listens to EventBus SelectionChanged/SelectionCleared events and opens graph context panel on entity selection.
function initSelectionSync() {
  const onChange = (event: import('../event-bus').RuntimeEvent) => {
    const entityId = (event.payload as { activeEntityId?: string | null }).activeEntityId ?? null;
    if (entityId && !graphInvocation.isOpen()) {
      // Auto-open context panel on selection (investigative, not navigation)
      graphInvocation.invoke({
        trigger: 'selection',
        entityId: String(entityId),
        mode: 'context-panel',
        maxNodes: 20,
        focusDepth: 1,
      });
    } else if (!entityId && graphInvocation.isOpen() && _activeScope?.trigger === 'selection') {
      // Close context panel when selection is cleared
      graphInvocation.close('selection-cleared');
    }
  };

  runtimeEventBus.subscribe(SELECTION_CHANGED, onChange);
  runtimeEventBus.subscribe(SELECTION_CLEARED, onChange);
}

// ===== Runtime Integration — WorkspaceSync =====
// Closes the graph overlay when the workspace switches.
// Graph is always scoped to the active workspace — it never persists across workspaces.
function initWorkspaceSync() {
  const checkWorkspace = () => {
    // Graph overlay must close on any workspace change (investigative-only invariant)
    if (graphInvocation.isOpen() && _activeScope?.mode === 'overlay') {
      graphInvocation.close('workspace-switched');
    }
  };

  window.addEventListener('os-workspace-changed', checkWorkspace);
  window.addEventListener('os-navigate-workspace', checkWorkspace);

  return () => {
    window.removeEventListener('os-workspace-changed', checkWorkspace);
    window.removeEventListener('os-navigate-workspace', checkWorkspace);
  };
}

// ===== Runtime Integration — Command Events =====
// Listens for os-graph-explore and os-graph-close custom events dispatched by command runtime.
function initCommandEventHandlers() {
  const exploreHandler = () => {
    const scope: GraphScope = {
      trigger: 'command',
      mode: 'overlay',
      focusDepth: 2,
    };
    graphInvocation.invoke(scope);
  };

  const closeHandler = () => {
    graphInvocation.close('command-close');
  };

  window.addEventListener('os-graph-explore', exploreHandler);
  window.addEventListener('os-graph-close', closeHandler);

  return () => {
    window.removeEventListener('os-graph-explore', exploreHandler);
    window.removeEventListener('os-graph-close', closeHandler);
  };
}

// ===== Runtime Integration — Keyboard Shortcut (Cmd/Ctrl+G) =====
// Architecture spec §6.6: Cmd/Ctrl+G opens graph overlay
function initKeyboardShortcut() {
  const handler = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'g' && !e.shiftKey && !e.altKey) {
      e.preventDefault();
      const scope: GraphScope = {
        trigger: 'command',
        mode: 'overlay',
        focusDepth: 2,
      };
      graphInvocation.invoke(scope);
    }
    // Escape closes graph
    if (e.key === 'Escape' && graphInvocation.isOpen()) {
      graphInvocation.close('escape');
    }
  };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}

// ===== Init =====
// These installers attach `window` event listeners, so they must not run during
// server-side rendering / static prerendering, where `window` is undefined.
if (typeof window !== 'undefined') {
  initSelectionSync();
  initWorkspaceSync();
  initCommandEventHandlers();
  initKeyboardShortcut();
}

// Export for module-level cleanup in tests
export function resetGraphInvocation() {
  graphInvocation.close('test-reset');
}
