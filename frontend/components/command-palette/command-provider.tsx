/**
 * Command Provider - Stage 5 Command Center Experience
 *
 * Provides command palette context to the application.
 * Uses CommandRuntime (lib/command/) as the single source of truth.
 */

'use client';

import { createContext, useContext, useMemo, useCallback, useEffect, useState } from 'react';
import type {
  CommandSearchResult,
  CommandHistoryEntry,
} from '@/lib/command/runtime';
import { commandRuntime } from '@/lib/command/command-runtime';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

// ===== Context Types =====
interface CommandContextValue {
  open: boolean;
  query: string;
  selectedIndex: number;
  filteredCommands: CommandSearchResult[];
  recentCommands: CommandHistoryEntry[];
  openPalette: () => void;
  closePalette: () => void;
  setQuery: (query: string) => void;
  selectNext: () => void;
  selectPrevious: () => void;
  executeSelected: () => Promise<void>;
  executeCommand: (input: string) => Promise<void>;
  navigateToWorkspace: (workspace: WorkspaceName) => void;
}

// ===== Context =====
const CommandContext = createContext<CommandContextValue | null>(null);

// ===== Provider =====
interface CommandProviderProps {
  children: React.ReactNode;
}

export function CommandProvider({ children }: CommandProviderProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [filteredCommands, setFilteredCommands] = useState<CommandSearchResult[]>([]);
  const [recentCommands, setRecentCommands] = useState<CommandHistoryEntry[]>([]);

  // Sync with command runtime
  useEffect(() => {
    const updateState = () => {
      const results = commandRuntime.search(query);
      setFilteredCommands(results);
      setSelectedIndex(0);
    };

    updateState();
    const unsubscribe = commandRuntime.subscribe(() => {
      const results = commandRuntime.search(query);
      setFilteredCommands(results);
      const recent = commandRuntime.getRecent(5);
      setRecentCommands(recent);
    });
    return unsubscribe;
  }, [query]);

  // Listen for os-open-command-palette event from CommandRuntime
  useEffect(() => {
    const handleOpen = () => {
      setOpen(true);
      setQuery('');
      setSelectedIndex(0);
      setFilteredCommands(commandRuntime.search(''));
    };
    window.addEventListener('os-open-command-palette', handleOpen);
    return () => window.removeEventListener('os-open-command-palette', handleOpen);
  }, []);

  // Load recent commands on mount
  useEffect(() => {
    setRecentCommands(commandRuntime.getRecent(5));
  }, []);

  const openPalette = useCallback(() => {
    setOpen(true);
    setQuery('');
    setSelectedIndex(0);
    setFilteredCommands(commandRuntime.search(''));
  }, []);

  const closePalette = useCallback(() => {
    setOpen(false);
    setQuery('');
    setSelectedIndex(0);
  }, []);

  const handleQueryChange = useCallback((newQuery: string) => {
    setQuery(newQuery);
    setSelectedIndex(0);
  }, []);

  const selectNext = useCallback(() => {
    setSelectedIndex(prev => (prev + 1) % Math.max(filteredCommands.length, 1));
  }, [filteredCommands.length]);

  const selectPrevious = useCallback(() => {
    setSelectedIndex(prev => (prev - 1 + Math.max(filteredCommands.length, 1)) % Math.max(filteredCommands.length, 1));
  }, [filteredCommands.length]);

  const executeSelected = useCallback(async () => {
    if (filteredCommands.length > 0) {
      const cmd = filteredCommands[selectedIndex].command;
      await commandRuntime.execute(cmd.id);
      closePalette();
    }
  }, [filteredCommands, selectedIndex, closePalette]);

  const executeCommand = useCallback(async (input: string) => {
    await commandRuntime.execute(input);
  }, []);

  const navigateToWorkspace = useCallback((workspace: WorkspaceName) => {
    commandRuntime.execute(`navigate ${workspace}`);
    window.location.href = `/${workspace}`;
  }, []);

  const value = useMemo<CommandContextValue>(
    () => ({
      open,
      query,
      selectedIndex,
      filteredCommands,
      recentCommands,
      openPalette,
      closePalette,
      setQuery: handleQueryChange,
      selectNext,
      selectPrevious,
      executeSelected,
      executeCommand,
      navigateToWorkspace,
    }),
    [open, query, selectedIndex, filteredCommands, recentCommands,
      openPalette, closePalette, handleQueryChange, selectNext, selectPrevious,
      executeSelected, executeCommand, navigateToWorkspace],
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