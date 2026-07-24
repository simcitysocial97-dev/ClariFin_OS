/**
 * useGlobalShortcuts - Stage 8F Financial OS Interaction Layer
 *
 * Hook for registering global keyboard shortcuts.
 * Uses the Keyboard Engine for all keyboard handling.
 */

import { useEffect, useCallback } from 'react';
import { keyboardEngine, registerKeyboardHandler } from '@/lib/interaction/keyboard-engine';
import { keyboardDispatcher } from '@/lib/interaction/keyboard-dispatcher';
import type { KeyboardShortcut, KeyboardHandler } from '@/lib/interaction/interaction-types';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

// ===== Hook =====
export function useGlobalShortcuts(
  shortcuts: KeyboardShortcut[],
  priority = 0,
  workspace?: WorkspaceName,
) {
  const handler: KeyboardHandler = {
    shortcuts,
    priority,
  };

  useEffect(() => {
    const handlerId = `custom:${workspace || 'global'}:${Date.now()}`;
    registerKeyboardHandler(handlerId, handler);

    return () => {
      keyboardEngine.unregisterHandler(handlerId);
    };
  }, [shortcuts, priority, workspace]);

  // Convenience methods
  const openCommandPalette = useCallback(() => {
    keyboardDispatcher.openCommandPalette();
  }, []);

  const openGlobalSearch = useCallback(() => {
    keyboardDispatcher.openGlobalSearch();
  }, []);

  const clearSelection = useCallback(() => {
    keyboardDispatcher.clearSelection();
  }, []);

  const focusSelectedNode = useCallback(() => {
    keyboardDispatcher.focusSelectedNode();
  }, []);

  const toggleOverlays = useCallback(() => {
    keyboardDispatcher.toggleOverlays();
  }, []);

  const toggleTimeline = useCallback(() => {
    keyboardDispatcher.toggleTimeline();
  }, []);

  const toggleInspector = useCallback(() => {
    keyboardDispatcher.toggleInspector();
  }, []);

  const navigateToWorkspace = useCallback((ws: WorkspaceName) => {
    keyboardDispatcher.navigateToWorkspace(ws);
  }, []);

  return {
    openCommandPalette,
    openGlobalSearch,
    clearSelection,
    focusSelectedNode,
    toggleOverlays,
    toggleTimeline,
    toggleInspector,
    navigateToWorkspace,
  };
}