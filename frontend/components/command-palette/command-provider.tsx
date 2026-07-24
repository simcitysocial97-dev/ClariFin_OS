/**
 * Command Provider - Stage 8F Financial OS Interaction Layer
 *
 * Provides command palette context to the application.
 * Discovers commands from WorkspaceRegistry.
 */

'use client';

import { createContext, useContext, useMemo, useCallback } from 'react';
import type { Command, CommandPaletteState } from '@/lib/command-center/command-palette';
import { commandPalette } from '@/lib/command-center/command-palette';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

// ===== Context Types =====
interface CommandContextValue {
  state: CommandPaletteState;
  commands: Command[];
  workspaceCommands: Record<WorkspaceName, Command[]>;
  openPalette: () => void;
  closePalette: () => void;
  setQuery: (query: string) => void;
  selectNext: () => void;
  selectPrevious: () => void;
  executeSelected: () => Promise<void>;
}

// ===== Context =====
const CommandContext = createContext<CommandContextValue | null>(null);

// ===== Provider =====
interface CommandProviderProps {
  children: React.ReactNode;
}

export function CommandProvider({ children }: CommandProviderProps) {
  // Subscribe to command palette state
  const state = commandPalette.getState();

  // Get all commands
  const commands = commandPalette.getAll();

  // Get commands grouped by workspace
  const workspaceCommands = useMemo(() => {
    const workspaces = workspaceRegistry.getAll();
    const result: Record<WorkspaceName, Command[]> = {} as Record<WorkspaceName, Command[]>;

    for (const workspace of workspaces) {
      // Get workspace-specific commands from the registry
      // These are derived from supportedCommands in WorkspaceRegistration
      result[workspace.name] = commands.filter(
        cmd => cmd.id.startsWith(`${workspace.name}:`) || cmd.description?.includes(workspace.label),
      );
    }

    return result;
  }, [commands]);

  // Actions
  const openPalette = useCallback(() => {
    commandPalette.openPalette();
  }, []);

  const closePalette = useCallback(() => {
    commandPalette.closePalette();
  }, []);

  const setQuery = useCallback((query: string) => {
    commandPalette.setQuery(query);
  }, []);

  const selectNext = useCallback(() => {
    commandPalette.selectNext();
  }, []);

  const selectPrevious = useCallback(() => {
    commandPalette.selectPrevious();
  }, []);

  const executeSelected = useCallback(async () => {
    await commandPalette.executeSelected();
  }, []);

  const value = useMemo<CommandContextValue>(
    () => ({
      state,
      commands,
      workspaceCommands,
      openPalette,
      closePalette,
      setQuery,
      selectNext,
      selectPrevious,
      executeSelected,
    }),
    [state, commands, workspaceCommands, openPalette, closePalette, setQuery, selectNext, selectPrevious, executeSelected],
  );

  return <CommandContext.Provider value={value}>{children}</CommandContext.Provider>;
}

// ===== Hook =====
export function useCommandContext(): CommandContextValue {
  const context = useContext(CommandContext);
  if (!context) {
    throw new Error('useCommandContext must be used within CommandProvider');
  }
  return context;
}