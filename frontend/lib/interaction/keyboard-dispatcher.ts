/**
 * Keyboard Dispatcher - Stage 8F Financial OS Interaction Layer
 *
 * Dispatches keyboard shortcuts to the appropriate runtime.
 * Routes through WorkspaceRegistry to find the correct handler.
 */

import type { KeyboardShortcut } from './interaction-types';
import type { WorkspaceName } from '../workspace';
import { workspaceRegistry } from '../workspace/workspace-registry';
import { commandCenterRuntime } from '../command-center';
import { commandPalette } from '../command-center/command-palette';
import { overlayRegistry } from '../../components/command-center/graph/overlay-registry';

// ===== Dispatcher State =====
interface DispatcherState {
  currentWorkspace: WorkspaceName;
}

// ===== Keyboard Dispatcher =====
class KeyboardDispatcher {
  private state: DispatcherState = {
    currentWorkspace: 'dashboard',
  };

  // ===== Workspace Management =====
  /**
   * Set the current workspace
   */
  setCurrentWorkspace(workspace: WorkspaceName): void {
    this.state.currentWorkspace = workspace;
  }

  /**
   * Get the current workspace
   */
  getCurrentWorkspace(): WorkspaceName {
    return this.state.currentWorkspace;
  }

  // ===== Shortcut Dispatching =====
  /**
   * Dispatch a shortcut to the appropriate handler
   */
  dispatch(shortcut: KeyboardShortcut): void {
    const workspace = workspaceRegistry.get(this.state.currentWorkspace);

    // Check if workspace has a specific handler for this shortcut
    if (workspace && workspace.keyboardShortcuts) {
      const command = Object.entries(workspace.keyboardShortcuts).find(
        ([key]) => key.toLowerCase() === shortcut.key.toLowerCase(),
      );

      if (command) {
        this.dispatchToWorkspace(command[1], workspace.name);
        return;
      }
    }

    // Default OS-level handling
    this.dispatchToOS();
  }

  // ===== Private Methods =====
  private dispatchToWorkspace(command: string, workspace: WorkspaceName): void {
    // Dispatch to workspace via custom event
    const event = new CustomEvent('workspace-command', {
      detail: { command, workspace },
    });
    window.dispatchEvent(event);
  }

  private dispatchToOS(): void {
    // OS-level shortcuts are handled by the shortcut itself
    // The handler is already defined in the shortcut
  }

  // ===== OS Actions =====
  /**
   * Open command palette
   */
  openCommandPalette(): void {
    commandPalette.openPalette();
  }

  /**
   * Open global search
   */
  openGlobalSearch(): void {
    const event = new CustomEvent('os-open-global-search');
    window.dispatchEvent(event);
  }

  /**
   * Clear selection
   */
  clearSelection(): void {
    commandCenterRuntime.clearSelection();
  }

  /**
   * Focus selected node
   */
  focusSelectedNode(): void {
    const selection = commandCenterRuntime.getSelection();
    if (selection.node_ids.length > 0) {
      const event = new CustomEvent('os-focus-node', {
        detail: { nodeId: selection.node_ids[0] },
      });
      window.dispatchEvent(event);
    }
  }

  /**
   * Toggle graph overlays
   */
  toggleOverlays(): void {
    const overlays = overlayRegistry.getAll();
    if (overlays.length > 0) {
      overlayRegistry.toggle(overlays[0].id);
    }
  }

  /**
   * Toggle timeline
   */
  toggleTimeline(): void {
    const event = new CustomEvent('os-toggle-timeline');
    window.dispatchEvent(event);
  }

  /**
   * Toggle inspector
   */
  toggleInspector(): void {
    const event = new CustomEvent('os-toggle-inspector');
    window.dispatchEvent(event);
  }

  /**
   * Navigate to workspace
   */
  navigateToWorkspace(workspace: WorkspaceName): void {
    this.setCurrentWorkspace(workspace);
    const event = new CustomEvent('os-navigate-workspace', {
      detail: { workspace },
    });
    window.dispatchEvent(event);
  }

  /**
   * Selection navigation
   */
  selectUp(): void {
    const event = new CustomEvent('os-selection-up');
    window.dispatchEvent(event);
  }

  selectDown(): void {
    const event = new CustomEvent('os-selection-down');
    window.dispatchEvent(event);
  }

  selectLeft(): void {
    const event = new CustomEvent('os-selection-left');
    window.dispatchEvent(event);
  }

  selectRight(): void {
    const event = new CustomEvent('os-selection-right');
    window.dispatchEvent(event);
  }

  /**
   * Inspect selected item
   */
  inspect(): void {
    const event = new CustomEvent('os-inspect');
    window.dispatchEvent(event);
  }

  /**
   * Center graph view
   */
  centerGraph(): void {
    const event = new CustomEvent('os-center-graph');
    window.dispatchEvent(event);
  }

  /**
   * Focus next element
   */
  focusNext(): void {
    const event = new CustomEvent('os-focus-next');
    window.dispatchEvent(event);
  }

  // ===== Reset =====
  /**
   * Reset the dispatcher
   */
  reset(): void {
    this.state = {
      currentWorkspace: 'dashboard',
    };
  }
}

// ===== Singleton Export =====
export const keyboardDispatcher = new KeyboardDispatcher();