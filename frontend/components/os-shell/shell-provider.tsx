/**
 * Shell Provider - Stage 8A Financial Operating System Shell
 *
 * React provider component for the OS Shell.
 * Integrates WorkspaceProvider with runtime connections.
 * No business logic - pure composition layer.
 */

'use client';

import { createContext, useContext, useMemo } from 'react';
import type { ReactNode } from 'react';
import { WorkspaceContext, useWorkspaceContext } from '@/lib/workspace/workspace-context';
import { commandCenterRuntime } from '@/lib/command-center';
import { performanceRuntime } from '@/lib/performance';
import { commandPalette } from '@/lib/command-center/command-palette';
import { layoutRuntime } from '@/lib/command-center/layout';
import { navigationRuntime } from '@/lib/command-center/navigation';
import type { WorkspaceContextValue } from '@/lib/workspace/workspace-context';

// ===== Shell Context =====
interface ShellContextValue {
  // Workspace context
  workspace: WorkspaceContextValue;
  // Runtime references (read-only)
  commandCenter: typeof commandCenterRuntime;
  performance: typeof performanceRuntime;
  commandPalette: typeof commandPalette;
  layout: typeof layoutRuntime;
  navigation: typeof navigationRuntime;
}

// ===== React Context =====
const ShellContext = createContext<ShellContextValue | null>(null);

// ===== Shell Provider Component =====
interface ShellProviderProps {
  children: ReactNode;
}

export function ShellProvider({ children }: ShellProviderProps) {
  // Get workspace context value - this creates the state
  // We then provide it via WorkspaceContext.Provider and ShellContext.Provider
  const workspace = useWorkspaceContext();

  const value = useMemo<ShellContextValue>(
    () => ({
      workspace,
      commandCenter: commandCenterRuntime,
      performance: performanceRuntime,
      commandPalette,
      layout: layoutRuntime,
      navigation: navigationRuntime,
    }),
    [workspace],
  );

  return (
    <WorkspaceContext.Provider value={workspace}>
      <ShellContext.Provider value={value}>{children}</ShellContext.Provider>
    </WorkspaceContext.Provider>
  );
}

// ===== Hook =====
export function useShell(): ShellContextValue {
  const context = useContext(ShellContext);
  if (!context) {
    throw new Error('useShell must be used within ShellProvider');
  }
  return context;
}