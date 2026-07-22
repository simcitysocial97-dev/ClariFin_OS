/**
 * useFocusEngine - Stage 8F Financial OS Interaction Layer
 *
 * Hook for focus management in the OS.
 * Every component can become focusable through this hook.
 */

import { useEffect, useCallback, useRef } from 'react';
import { focusEngine, type FocusableElement } from '@/lib/interaction/focus-engine';
import type { FocusTarget } from '@/lib/interaction/interaction-types';

// ===== Hook =====
export function useFocusEngine(
  id: string,
  type: FocusTarget,
  priority = 0,
  autoRegister = true,
) {
  const elementRef = useRef<HTMLElement>(null);

  // Register the element for focus management
  useEffect(() => {
    if (!autoRegister) return;

    const element = elementRef.current;
    if (!element) return;

    const focusable: FocusableElement = {
      id,
      type,
      element,
      priority,
    };

    focusEngine.register(focusable);

    return () => {
      focusEngine.unregister(id);
    };
  }, [id, type, priority, autoRegister]);

  // Focus methods
  const focus = useCallback(() => {
    focusEngine.focus(id);
  }, [id]);

  const focusNext = useCallback(() => {
    focusEngine.focusNext();
  }, []);

  const focusPrevious = useCallback(() => {
    focusEngine.focusPrevious();
  }, []);

  const focusFirst = useCallback(() => {
    focusEngine.focusFirst();
  }, []);

  const focusLast = useCallback(() => {
    focusEngine.focusLast();
  }, []);

  const clearFocus = useCallback(() => {
    focusEngine.clearFocus();
  }, []);

  // Type-specific focus methods
  const focusPanel = useCallback((panelId: string) => {
    focusEngine.focusPanel(panelId);
  }, []);

  const focusWidget = useCallback((widgetId: string) => {
    focusEngine.focusWidget(widgetId);
  }, []);

  const focusGraph = useCallback(() => {
    focusEngine.focusGraph();
  }, []);

  const focusTable = useCallback((tableId: string) => {
    focusEngine.focusTable(tableId);
  }, []);

  const focusTimeline = useCallback(() => {
    focusEngine.focusTimeline();
  }, []);

  const focusInspector = useCallback(() => {
    focusEngine.focusInspector();
  }, []);

  const focusSearch = useCallback(() => {
    focusEngine.focusSearch();
  }, []);

  return {
    elementRef,
    focus,
    focusNext,
    focusPrevious,
    focusFirst,
    focusLast,
    clearFocus,
    focusPanel,
    focusWidget,
    focusGraph,
    focusTable,
    focusTimeline,
    focusInspector,
    focusSearch,
  };
}