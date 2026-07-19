/**
 * Navigation Keyboard Shortcuts - Stage 3 Transaction Intelligence Workspace
 *
 * Keyboard navigation utilities for the workspace.
 * Supports Alt+Arrow keys for navigation.
 */

import { useEffect } from 'react';

/**
 * Navigation keyboard shortcut configuration
 */
export interface NavigationKeyboardShortcuts {
  onBack?: () => void;
  onForward?: () => void;
  onUp?: () => void;
  onDown?: () => void;
}

/**
 * Hook to handle navigation keyboard shortcuts
 * Alt+ArrowLeft: Go back
 * Alt+ArrowRight: Go forward
 * Alt+ArrowUp: Navigate up
 * Alt+ArrowDown: Navigate down
 */
export function useNavigationKeyboardShortcuts(
  shortcuts: NavigationKeyboardShortcuts
): void {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip if focus is on an input or select element
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLSelectElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Alt+ArrowLeft: Go back
      if (event.altKey && event.key === 'ArrowLeft') {
        event.preventDefault();
        shortcuts.onBack?.();
      }

      // Alt+ArrowRight: Go forward
      if (event.altKey && event.key === 'ArrowRight') {
        event.preventDefault();
        shortcuts.onForward?.();
      }

      // Alt+ArrowUp: Navigate up
      if (event.altKey && event.key === 'ArrowUp') {
        event.preventDefault();
        shortcuts.onUp?.();
      }

      // Alt+ArrowDown: Navigate down
      if (event.altKey && event.key === 'ArrowDown') {
        event.preventDefault();
        shortcuts.onDown?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

/**
 * Check if a keyboard event matches a navigation shortcut
 */
export function isNavigationShortcut(event: KeyboardEvent): boolean {
  return event.altKey && (
    event.key === 'ArrowLeft' ||
    event.key === 'ArrowRight' ||
    event.key === 'ArrowUp' ||
    event.key === 'ArrowDown'
  );
}