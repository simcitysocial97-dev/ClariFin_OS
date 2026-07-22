/**
 * Keyboard Engine - Stage 8F Financial OS Interaction Layer
 *
 * The single source of truth for all keyboard events in the OS.
 * No workspace may attach document keydown listeners.
 *
 * Architecture: Browser → Keyboard Engine → Dispatcher → Workspace Registry → Runtime
 */

import type { KeyboardShortcut, KeyboardHandler } from './interaction-types';
import { keyboardRegistry } from './keyboard-registry';

// ===== Keyboard Engine State =====
interface KeyboardEngineState {
  enabled: boolean;
  activeModifiers: {
    ctrl: boolean;
    cmd: boolean;
    alt: boolean;
    shift: boolean;
  };
}

// ===== Component Keyboard Handler =====
export interface ComponentKeyboardHandler {
  id: string;
  shortcuts: KeyboardShortcut[];
  // Element selector to check if focus is within this component
  elementSelector?: string;
  // Priority (higher = checked first)
  priority?: number;
}

// ===== Keyboard Engine =====
class KeyboardEngine {
  private state: KeyboardEngineState = {
    enabled: true,
    activeModifiers: {
      ctrl: false,
      cmd: false,
      alt: false,
      shift: false,
    },
  };

  private handlers: Map<string, KeyboardHandler> = new Map();
  private componentHandlers: Map<string, ComponentKeyboardHandler> = new Map();

  // ===== Registration =====
  /**
   * Register a keyboard handler with priority
   */
  registerHandler(id: string, handler: KeyboardHandler): void {
    this.handlers.set(id, handler);
  }

  /**
   * Unregister a keyboard handler
   */
  unregisterHandler(id: string): boolean {
    return this.handlers.delete(id);
  }

  /**
   * Register a component-level keyboard handler
   * These handlers only fire when focus is within the specified element
   */
  registerComponentHandler(handler: ComponentKeyboardHandler): void {
    this.componentHandlers.set(handler.id, {
      ...handler,
      priority: handler.priority ?? 0,
    });
  }

  /**
   * Unregister a component-level keyboard handler
   */
  unregisterComponentHandler(id: string): boolean {
    return this.componentHandlers.delete(id);
  }

  // ===== Event Handling =====
  /**
   * Handle a keyboard event - the single entry point for all keyboard input
   */
  handleKeyDown(event: KeyboardEvent): void {
    if (!this.state.enabled) return;

    // Update active modifiers
    this.updateModifiers(event);

    // Check component-level handlers first (for focused components)
    const componentShortcut = this.findComponentShortcut(event);
    if (componentShortcut) {
      event.preventDefault();
      event.stopPropagation();
      this.executeShortcut(componentShortcut, event);
      return;
    }

    // Don't handle if focus is on input/textarea (let them handle their own input)
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return;
    }

    // Find matching shortcut
    const shortcut = this.findMatchingShortcut(event);
    if (shortcut) {
      event.preventDefault();
      event.stopPropagation();
      this.executeShortcut(shortcut, event);
    }
  }

  // ===== Private Methods =====
  private updateModifiers(event: KeyboardEvent): void {
    this.state.activeModifiers = {
      ctrl: event.ctrlKey,
      cmd: event.metaKey,
      alt: event.altKey,
      shift: event.shiftKey,
    };
  }

  private findComponentShortcut(event: KeyboardEvent): KeyboardShortcut | null {
    const activeElement = document.activeElement;
    if (!activeElement) return null;

    // Get all component handlers sorted by priority
    const sortedHandlers = Array.from(this.componentHandlers.values()).sort(
      (a, b) => (b.priority ?? 0) - (a.priority ?? 0),
    );

    for (const handler of sortedHandlers) {
      // Check if focus is within this component
      if (handler.elementSelector) {
        const closest = activeElement.closest(handler.elementSelector);
        if (!closest) continue;
      }

      // Check for matching shortcut
      for (const shortcut of handler.shortcuts) {
        if (this.matchesShortcut(event, shortcut)) {
          return shortcut;
        }
      }
    }

    return null;
  }

  private findMatchingShortcut(event: KeyboardEvent): KeyboardShortcut | null {
    const allShortcuts = this.getAllShortcuts();
    const isMac = navigator.platform.includes('Mac');

    for (const shortcut of allShortcuts) {
      // Check key match
      if (shortcut.key.toLowerCase() !== event.key.toLowerCase()) continue;

      // Check modifier match
      const ctrlMatch = isMac
        ? (shortcut.cmd ?? false) === event.metaKey
        : (shortcut.ctrl ?? false) === event.ctrlKey;

      if (!ctrlMatch) continue;
      if ((shortcut.alt ?? false) !== event.altKey) continue;
      if ((shortcut.shift ?? false) !== event.shiftKey) continue;

      return shortcut;
    }

    return null;
  }

  private matchesShortcut(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
    // Check key match
    if (shortcut.key.toLowerCase() !== event.key.toLowerCase()) return false;

    // Check modifier match
    const isMac = navigator.platform.includes('Mac');
    const ctrlMatch = isMac
      ? (shortcut.cmd ?? false) === event.metaKey
      : (shortcut.ctrl ?? false) === event.ctrlKey;

    if (!ctrlMatch) return false;
    if ((shortcut.alt ?? false) !== event.altKey) return false;
    if ((shortcut.shift ?? false) !== event.shiftKey) return false;

    return true;
  }

  private getAllShortcuts(): KeyboardShortcut[] {
    const shortcuts: KeyboardShortcut[] = [];
    const sortedHandlers = Array.from(this.handlers.values()).sort(
      (a, b) => b.priority - a.priority,
    );

    for (const handler of sortedHandlers) {
      shortcuts.push(...handler.shortcuts);
    }

    return shortcuts;
  }

  private executeShortcut(shortcut: KeyboardShortcut, event: KeyboardEvent): void {
    // Also register with the registry for tracking
    keyboardRegistry.recordUsage(shortcut);

    // Execute the handler
    shortcut.handler(event);
  }

  // ===== Control =====
  /**
   * Enable keyboard handling
   */
  enable(): void {
    this.state.enabled = true;
  }

  /**
   * Disable keyboard handling
   */
  disable(): void {
    this.state.enabled = false;
  }

  /**
   * Check if keyboard handling is enabled
   */
  isEnabled(): boolean {
    return this.state.enabled;
  }

  /**
   * Get current state
   */
  getState(): KeyboardEngineState {
    return { ...this.state };
  }

  // ===== Reset =====
  /**
   * Reset the keyboard engine
   */
  reset(): void {
    this.handlers.clear();
    this.componentHandlers.clear();
    this.state = {
      enabled: true,
      activeModifiers: {
        ctrl: false,
        cmd: false,
        alt: false,
        shift: false,
      },
    };
  }
}

// ===== Singleton Export =====
export const keyboardEngine = new KeyboardEngine();

// ===== Initialization =====
/**
 * Initialize the keyboard engine - call once at app startup
 */
export function initKeyboardEngine(): void {
  if (typeof window === 'undefined') return;

  // Attach global keydown listener
  window.addEventListener('keydown', (event) => {
    keyboardEngine.handleKeyDown(event);
  });
}

// ===== Convenience Functions =====
export function registerKeyboardHandler(id: string, handler: KeyboardHandler): void {
  keyboardEngine.registerHandler(id, handler);
}

export function unregisterKeyboardHandler(id: string): boolean {
  return keyboardEngine.unregisterHandler(id);
}

export function registerComponentKeyboardHandler(handler: ComponentKeyboardHandler): void {
  keyboardEngine.registerComponentHandler(handler);
}

export function unregisterComponentKeyboardHandler(id: string): boolean {
  return keyboardEngine.unregisterComponentHandler(id);
}