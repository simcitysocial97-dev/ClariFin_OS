/**
 * Keyboard Platform - Stage 8C Financial OS Visual System
 *
 * Cross-cutting keyboard navigation and shortcuts.
 */

// ===== Keyboard Shortcuts =====
export const keyboardShortcuts = {
  // Graph navigation
  graph: {
    focus: 'f',
    search: 's',
    zoomIn: '+',
    zoomOut: '-',
    reset: '0',
    tree: 't',
    force: 'g',
    timeline: 'l',
  },
  // General
  general: {
    help: '?',
    settings: 'ctrl+/',
  },
} as const;

// ===== Keyboard Event Handler =====
export function createKeyboardHandler(
  onFocus: () => void,
  onSearch: () => void,
  onZoomIn: () => void,
  onZoomOut: () => void,
  onReset: () => void,
) {
  return (event: KeyboardEvent) => {
    if (event.target instanceof HTMLInputElement) return;

    const key = event.key.toLowerCase();

    switch (key) {
      case keyboardShortcuts.graph.focus:
        onFocus();
        break;
      case keyboardShortcuts.graph.search:
        onSearch();
        break;
      case keyboardShortcuts.graph.zoomIn:
        onZoomIn();
        break;
      case keyboardShortcuts.graph.zoomOut:
        onZoomOut();
        break;
      case keyboardShortcuts.graph.reset:
        onReset();
        break;
    }
  };
}