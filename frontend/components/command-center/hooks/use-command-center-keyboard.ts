/**
 * Command Center Keyboard - Stage 8E-B Command Center
 *
 * Keyboard shortcuts for the Command Center workspace.
 * Integrates with the OS-level keyboard system.
 */

import { useEffect, useCallback } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import { overlayRegistry } from '../graph/overlay-registry';

// ===== Keyboard Map =====
export interface CommandCenterKeyboardMap {
  ArrowUp: () => void;
  ArrowDown: () => void;
  ArrowLeft: () => void;
  ArrowRight: () => void;
  Enter: () => void;
  Space: () => void;
  Escape: () => void;
  'Ctrl+K': () => void;
  'Cmd+K': () => void;
  f: () => void;
  g: () => void;
}

// ===== Hook =====
export function useCommandCenterKeyboard(
  onNodeSelect?: (nodeId: string) => void,
  onNodeFocus?: (nodeId: string) => void,
) {
  // Get current selection
  const selection = commandCenterRuntime.getSelection();
  const graph = commandCenterRuntime.getCurrentGraph();

  // Handle arrow keys - graph traversal
  const handleArrowUp = useCallback(() => {
    // Move selection up in graph
  }, []);

  const handleArrowDown = useCallback(() => {
    // Move selection down in graph
  }, []);

  const handleArrowLeft = useCallback(() => {
    // Move selection left in graph
  }, []);

  const handleArrowRight = useCallback(() => {
    // Move selection right in graph
  }, []);

  // Handle Enter - inspect entity
  const handleEnter = useCallback(() => {
    if (selection.node_ids.length > 0) {
      onNodeSelect?.(selection.node_ids[0]);
    }
  }, [selection.node_ids, onNodeSelect]);

  // Handle Space - focus graph
  const handleSpace = useCallback(() => {
    // Focus the graph view
    const event = new CustomEvent('command-center-focus-graph');
    window.dispatchEvent(event);
  }, []);

  // Handle Escape - clear selection
  const handleEscape = useCallback(() => {
    commandCenterRuntime.clearSelection();
  }, []);

  // Handle Ctrl/Cmd+K - command palette
  const handleCommandPalette = useCallback(() => {
    const event = new CustomEvent('command-center-open-palette');
    window.dispatchEvent(event);
  }, []);

  // Handle F - focus selected node
  const handleFocusNode = useCallback(() => {
    if (selection.node_ids.length > 0) {
      onNodeFocus?.(selection.node_ids[0]);
    }
  }, [selection.node_ids, onNodeFocus]);

  // Handle G - toggle graph overlays
  const handleToggleOverlays = useCallback(() => {
    const overlays = overlayRegistry.getAll();
    if (overlays.length > 0) {
      overlayRegistry.toggle(overlays[0].id);
    }
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't handle if focus is on input
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      const isMac = navigator.platform.includes('Mac');
      const ctrlKey = isMac ? event.metaKey : event.ctrlKey;

      switch (event.key) {
        case 'ArrowUp':
          event.preventDefault();
          handleArrowUp();
          break;
        case 'ArrowDown':
          event.preventDefault();
          handleArrowDown();
          break;
        case 'ArrowLeft':
          event.preventDefault();
          handleArrowLeft();
          break;
        case 'ArrowRight':
          event.preventDefault();
          handleArrowRight();
          break;
        case 'Enter':
          event.preventDefault();
          handleEnter();
          break;
        case ' ':
          event.preventDefault();
          handleSpace();
          break;
        case 'Escape':
          event.preventDefault();
          handleEscape();
          break;
        case 'f':
        case 'F':
          if (!event.shiftKey && !event.altKey) {
            event.preventDefault();
            handleFocusNode();
          }
          break;
        case 'g':
        case 'G':
          if (!event.shiftKey && !event.altKey) {
            event.preventDefault();
            handleToggleOverlays();
          }
          break;
        case 'k':
        case 'K':
          if (ctrlKey) {
            event.preventDefault();
            handleCommandPalette();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    handleArrowUp,
    handleArrowDown,
    handleArrowLeft,
    handleArrowRight,
    handleEnter,
    handleSpace,
    handleEscape,
    handleFocusNode,
    handleToggleOverlays,
    handleCommandPalette,
  ]);

  return {
    selection,
    graph,
  };
}