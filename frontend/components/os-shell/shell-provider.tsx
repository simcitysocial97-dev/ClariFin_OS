/**
 * Shell Provider - Stage 8A Financial Operating System Shell
 *
 * React provider component for the OS Shell.
 * Integrates WorkspaceProvider with runtime connections.
 * No business logic - pure composition layer.
 *
 * Stage 8F: Now includes interaction layer providers.
 */

'use client';

import { createContext, useContext, useMemo, useEffect } from 'react';
import type { ReactNode } from 'react';
import { WorkspaceContext, useWorkspaceContext } from '@/lib/workspace/workspace-context';
import { commandCenterRuntime } from '@/lib/command-center';
import { performanceRuntime } from '@/lib/performance';
import { commandPalette } from '@/lib/command-center/command-palette';
import { layoutRuntime } from '@/lib/command-center/layout';
import { navigationRuntime } from '@/lib/command-center/navigation';
import { initKeyboardEngine, keyboardEngine } from '@/lib/interaction/keyboard-engine';
import { createDefaultShortcuts } from '@/lib/interaction/keyboard-registry';
import { keyboardDispatcher } from '@/lib/interaction/keyboard-dispatcher';
import { initDefaultOverlays } from '@/components/interaction/overlay-manager';
import { CommandProvider } from '@/components/command-palette/command-provider';
import { SearchProvider } from '@/components/global-search/search-provider';
import { DensityProvider } from '@/components/interaction/density-provider';
import { CommandPalette } from '@/components/command-palette/command-palette';
import { GlobalSearch } from '@/components/global-search/global-search';
import { ShortcutOverlay } from '@/components/interaction/shortcut-overlay';
import { applyDensityVariables } from '@/components/interaction/density-provider';
import type { WorkspaceContextValue } from '@/lib/workspace/workspace-context';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

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

  // Initialize keyboard engine and default shortcuts on mount
  useEffect(() => {
    // Initialize keyboard engine
    initKeyboardEngine();

    // Initialize default overlays
    initDefaultOverlays();

    // Register default shortcuts with the keyboard engine
    const shortcuts = createDefaultShortcuts(
      (ws: WorkspaceName) => keyboardDispatcher.navigateToWorkspace(ws),
      () => keyboardDispatcher.openCommandPalette(),
      () => keyboardDispatcher.openGlobalSearch(),
      () => keyboardDispatcher.clearSelection(),
      () => keyboardDispatcher.focusSelectedNode(),
      () => keyboardDispatcher.toggleOverlays(),
      () => keyboardDispatcher.toggleTimeline(),
      () => keyboardDispatcher.toggleInspector(),
    );

    // Create a handler for the default shortcuts
    const defaultHandler = {
      shortcuts,
      priority: 100, // High priority for OS-level shortcuts
    };
    keyboardEngine.registerHandler('os-default', defaultHandler);

    // Apply initial density variables
    applyDensityVariables('comfortable');
  }, []);

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
      <ShellContext.Provider value={value}>
        <DensityProvider>
          <SearchProvider>
            <CommandProvider>
              {children}
              {/* Interaction Overlays - rendered at shell level */}
              <CommandPalette />
              <GlobalSearch />
              <ShortcutOverlay />
            </CommandProvider>
          </SearchProvider>
        </DensityProvider>
      </ShellContext.Provider>
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