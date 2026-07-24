/**
 * Focus Engine - Stage 8F Financial OS Interaction Layer
 *
 * Central focus management for the entire OS.
 * Every component becomes focusable through this engine.
 *
 * Supports: Tab, Shift+Tab, Arrow, Home, End, Escape
 */

import type { FocusTarget, FocusState } from './interaction-types';

// ===== Focusable Element =====
export interface FocusableElement {
  id: string;
  type: FocusTarget;
  element: HTMLElement | null;
  priority: number;
}

// ===== Focus Engine =====
class FocusEngine {
  private state: FocusState = {
    currentTarget: null,
    currentElementId: null,
    cycleIndex: 0,
  };

  private elements: Map<string, FocusableElement> = new Map();
  private listeners: Array<(state: FocusState) => void> = [];

  // ===== Registration =====
  /**
   * Register a focusable element
   */
  register(element: FocusableElement): void {
    this.elements.set(element.id, element);
  }

  /**
   * Unregister a focusable element
   */
  unregister(id: string): boolean {
    return this.elements.delete(id);
  }

  /**
   * Get a focusable element by ID
   */
  get(id: string): FocusableElement | undefined {
    return this.elements.get(id);
  }

  /**
   * Get all focusable elements
   */
  getAll(): FocusableElement[] {
    return Array.from(this.elements.values());
  }

  /**
   * Get elements by type
   */
  getByType(type: FocusTarget): FocusableElement[] {
    return this.getAll().filter(e => e.type === type);
  }

  // ===== Focus Management =====
  /**
   * Focus a specific element
   */
  focus(id: string): void {
    const element = this.elements.get(id);
    if (element?.element) {
      element.element.focus();
      this.state = {
        ...this.state,
        currentTarget: element.type,
        currentElementId: id,
      };
      this.notify();
    }
  }

  /**
   * Focus next element (Tab)
   */
  focusNext(): void {
    const sorted = this.getSortedElements();
    if (sorted.length === 0) return;

    this.state.cycleIndex = (this.state.cycleIndex + 1) % sorted.length;
    const next = sorted[this.state.cycleIndex];
    this.focus(next.id);
  }

  /**
   * Focus previous element (Shift+Tab)
   */
  focusPrevious(): void {
    const sorted = this.getSortedElements();
    if (sorted.length === 0) return;

    this.state.cycleIndex = (this.state.cycleIndex - 1 + sorted.length) % sorted.length;
    const prev = sorted[this.state.cycleIndex];
    this.focus(prev.id);
  }

  /**
   * Focus first element (Home)
   */
  focusFirst(): void {
    const sorted = this.getSortedElements();
    if (sorted.length > 0) {
      this.state.cycleIndex = 0;
      this.focus(sorted[0].id);
    }
  }

  /**
   * Focus last element (End)
   */
  focusLast(): void {
    const sorted = this.getSortedElements();
    if (sorted.length > 0) {
      this.state.cycleIndex = sorted.length - 1;
      this.focus(sorted[sorted.length - 1].id);
    }
  }

  /**
   * Clear focus (Escape)
   */
  clearFocus(): void {
    this.state = {
      ...this.state,
      currentTarget: null,
      currentElementId: null,
      cycleIndex: 0,
    };
    this.notify();
  }

  // ===== Focus Targets =====
  /**
   * Focus panel
   */
  focusPanel(panelId: string): void {
    this.focus(`panel:${panelId}`);
  }

  /**
   * Focus widget
   */
  focusWidget(widgetId: string): void {
    this.focus(`widget:${widgetId}`);
  }

  /**
   * Focus graph
   */
  focusGraph(): void {
    this.focus('graph:canvas');
  }

  /**
   * Focus table
   */
  focusTable(tableId: string): void {
    this.focus(`table:${tableId}`);
  }

  /**
   * Focus timeline
   */
  focusTimeline(): void {
    this.focus('timeline:container');
  }

  /**
   * Focus inspector
   */
  focusInspector(): void {
    this.focus('inspector:container');
  }

  /**
   * Focus search
   */
  focusSearch(): void {
    this.focus('search:input');
  }

  // ===== State =====
  /**
   * Get current focus state
   */
  getState(): FocusState {
    return { ...this.state };
  }

  // ===== Subscription =====
  /**
   * Subscribe to focus changes
   */
  subscribe(listener: (state: FocusState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  // ===== Private Methods =====
  private getSortedElements(): FocusableElement[] {
    return this.getAll().sort((a, b) => a.priority - b.priority);
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener(this.getState());
    }
  }

  // ===== Reset =====
  /**
   * Reset the focus engine
   */
  reset(): void {
    this.elements.clear();
    this.state = {
      currentTarget: null,
      currentElementId: null,
      cycleIndex: 0,
    };
    this.notify();
  }
}

// ===== Singleton Export =====
export const focusEngine = new FocusEngine();

// ===== Convenience Functions =====
export function registerFocusable(
  id: string,
  type: FocusTarget,
  element: HTMLElement | null,
  priority = 0,
): void {
  focusEngine.register({ id, type, element, priority });
}

export function unregisterFocusable(id: string): void {
  focusEngine.unregister(id);
}