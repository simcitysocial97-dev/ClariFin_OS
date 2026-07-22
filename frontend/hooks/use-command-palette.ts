/**
 * useCommandPalette - Stage 8F Financial OS Interaction Layer
 *
 * Hook for command palette integration.
 * Discovers commands from WorkspaceRegistry.
 */

import { useEffect, useCallback, useMemo } from 'react';
import { commandPalette } from '@/lib/command-center/command-palette';
import { workspaceRegistry } from '@/lib/workspace/workspace-registry';
import type { Command } from '@/lib/command-center/command-palette';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

// ===== Hook =====
export function useCommandPalette(workspace?: WorkspaceName) {
  // Get workspace commands
  const workspaceCommands = useMemo(() => {
    if (!workspace) return [];
    const reg = workspaceRegistry.get(workspace);
    if (!reg) return [];

    // Convert supportedCommands to Command objects
    return reg.supportedCommands.map((cmd) => ({
      id: `${workspace}:${cmd}`,
      label: cmd.charAt(0).toUpperCase() + cmd.slice(1),
      description: `${cmd} in ${reg.label}`,
      category: 'workspace' as const,
      handler: () => {
        const event = new CustomEvent('workspace-command', {
          detail: { command: cmd, workspace },
        });
        window.dispatchEvent(event);
      },
    }));
  }, [workspace]);

  // Register workspace commands
  useEffect(() => {
    if (workspaceCommands.length > 0) {
      commandPalette.registerAll(workspaceCommands);
    }

    return () => {
      workspaceCommands.forEach(cmd => {
        commandPalette.unregister(cmd.id);
      });
    };
  }, [workspaceCommands]);

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

  // Get all commands
  const getAllCommands = useCallback((): Command[] => {
    return commandPalette.getAll();
  }, []);

  // Get commands by category
  const getCommandsByCategory = useCallback((category: Command['category']): Command[] => {
    return commandPalette.getByCategory(category);
  }, []);

  return {
    openPalette,
    closePalette,
    setQuery,
    selectNext,
    selectPrevious,
    executeSelected,
    getAllCommands,
    getCommandsByCategory,
    workspaceCommands,
  };
}