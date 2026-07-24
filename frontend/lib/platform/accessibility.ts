/**
 * Accessibility Platform - Stage 8C Financial OS Visual System
 *
 * Cross-cutting accessibility utilities.
 */

// ===== ARIA Labels =====
export function getGraphAriaLabel(nodeCount: number, edgeCount: number): string {
  return `Financial graph with ${nodeCount} nodes and ${edgeCount} connections`;
}

export function getNodeAriaLabel(label: string, valuePaise?: number, confidence?: number): string {
  const value = valuePaise !== undefined ? ` value ${(valuePaise / 100).toFixed(2)} rupees` : '';
  const conf = confidence !== undefined ? ` confidence ${confidence}%` : '';
  return `${label}${value}${conf}`;
}

// ===== Focus Management =====
export function focusElement(elementId: string): void {
  const element = document.getElementById(elementId);
  if (element) {
    element.focus();
  }
}

// ===== Keyboard Navigation =====
export function isKeyboardNavigation(): boolean {
  return typeof window !== 'undefined' && (document.activeElement?.classList.contains('keyboard-navigation') ?? false);
}
