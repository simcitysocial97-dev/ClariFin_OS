/**
 * Command Palette - Stage 7.5 Runtime Consolidation
 *
 * Universal operating interface for the Financial Operating System.
 * Provides a single command interface across all workspaces.
 *
 * Architecture: CommandPalette → Command Registry → Workspace Actions
 */

import type { WorkspaceName } from '../workspace';

// ===== Command Types =====
export type CommandCategory =
  | 'navigation'
  | 'workspace'
  | 'graph'
  | 'filter'
  | 'selection'
  | 'evidence'
  | 'performance'
  | 'system';

export interface Command {
  id: string;
  label: string;
  description?: string;
  category: CommandCategory;
  icon?: string;
  shortcut?: string;
  handler: () => void | Promise<void>;
  disabled?: () => boolean;
  hidden?: () => boolean;
}

export interface CommandGroup {
  id: string;
  label: string;
  category: CommandCategory;
  commands: Command[];
}

export interface CommandPaletteState {
  open: boolean;
  query: string;
  selectedIndex: number;
  filteredCommands: Command[];
}

// ===== Command Palette =====
/**
 * Main command palette for the Financial Operating System.
 * Provides a universal interface for all workspace operations.
 */
export class CommandPalette {
  private commands: Map<string, Command> = new Map();
  private groups: Map<string, CommandGroup> = new Map();
  private state: CommandPaletteState = {
    open: false,
    query: '',
    selectedIndex: 0,
    filteredCommands: [],
  };
  private listeners: Array<(state: CommandPaletteState) => void> = [];

  // ===== Registration =====
  /**
   * Register a command
   */
  register(command: Command): void {
    this.commands.set(command.id, command);
    this.updateFiltered();
  }

  /**
   * Register multiple commands
   */
  registerAll(commands: Command[]): void {
    for (const command of commands) {
      this.register(command);
    }
  }

  /**
   * Unregister a command
   */
  unregister(commandId: string): boolean {
    const result = this.commands.delete(commandId);
    this.updateFiltered();
    return result;
  }

  /**
   * Get a command by ID
   */
  get(commandId: string): Command | undefined {
    return this.commands.get(commandId);
  }

  /**
   * Get all registered commands
   */
  getAll(): Command[] {
    return Array.from(this.commands.values());
  }

  /**
   * Get commands by category
   */
  getByCategory(category: CommandCategory): Command[] {
    return Array.from(this.commands.values()).filter(
      cmd => cmd.category === category,
    );
  }

  // ===== State Management =====
  /**
   * Open the command palette
   */
  openPalette(): void {
    this.state = {
      ...this.state,
      open: true,
      query: '',
      selectedIndex: 0,
    };
    this.updateFiltered();
    this.notify();
  }

  /**
   * Close the command palette
   */
  closePalette(): void {
    this.state = {
      ...this.state,
      open: false,
      query: '',
      selectedIndex: 0,
    };
    this.notify();
  }

  /**
   * Toggle the command palette
   */
  togglePalette(): void {
    if (this.state.open) {
      this.closePalette();
    } else {
      this.openPalette();
    }
  }

  /**
   * Set the search query
   */
  setQuery(query: string): void {
    this.state = {
      ...this.state,
      query,
      selectedIndex: 0,
    };
    this.updateFiltered();
    this.notify();
  }

  /**
   * Select next command
   */
  selectNext(): void {
    this.state = {
      ...this.state,
      selectedIndex:
        (this.state.selectedIndex + 1) % this.state.filteredCommands.length,
    };
    this.notify();
  }

  /**
   * Select previous command
   */
  selectPrevious(): void {
    this.state = {
      ...this.state,
      selectedIndex:
        (this.state.selectedIndex - 1 + this.state.filteredCommands.length) %
        this.state.filteredCommands.length,
    };
    this.notify();
  }

  /**
   * Execute the selected command
   */
  async executeSelected(): Promise<void> {
    const command = this.state.filteredCommands[this.state.selectedIndex];
    if (command && !command.disabled?.()) {
      this.closePalette();
      await command.handler();
    }
  }

  /**
   * Get current state
   */
  getState(): CommandPaletteState {
    return { ...this.state };
  }

  // ===== Subscription =====
  /**
   * Subscribe to state changes
   */
  subscribe(listener: (state: CommandPaletteState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  // ===== Private Methods =====
  private updateFiltered(): void {
    const query = this.state.query.toLowerCase();
    this.state.filteredCommands = this.getAll().filter(cmd => {
      if (cmd.hidden?.()) return false;
      if (!query) return true;
      return (
        cmd.label.toLowerCase().includes(query) ||
        cmd.description?.toLowerCase().includes(query) ||
        cmd.category.toLowerCase().includes(query)
      );
    });
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener(this.getState());
    }
  }

  // ===== Reset =====
  /**
   * Reset the command palette
   */
  reset(): void {
    this.commands.clear();
    this.groups.clear();
    this.state = {
      open: false,
      query: '',
      selectedIndex: 0,
      filteredCommands: [],
    };
    this.notify();
  }
}

// ===== Convenience Export =====
export const commandPalette = new CommandPalette();

// ===== Default Commands =====
/**
 * Create default system commands
 */
export function createDefaultCommands(
  _onNavigate?: (workspace: WorkspaceName) => void,
): Command[] {
  return [
    {
      id: 'toggle-sidebar',
      label: 'Toggle Sidebar',
      description: 'Show or hide the sidebar',
      category: 'navigation',
      shortcut: 'Ctrl+B',
      handler: () => {
        // This would be implemented by the UI layer
        console.log('Toggle sidebar');
      },
    },
    {
      id: 'open-command-palette',
      label: 'Open Command Palette',
      description: 'Open the command palette',
      category: 'system',
      shortcut: 'Ctrl+K',
      handler: () => {
        commandPalette.openPalette();
      },
    },
    {
      id: 'clear-cache',
      label: 'Clear Cache',
      description: 'Clear the performance cache',
      category: 'performance',
      handler: () => {
        // This would be implemented by the UI layer
        console.log('Clear cache');
      },
    },
  ];
}