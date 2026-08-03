/**
 * Runtime Provider - Single composition layer for all runtimes.
 * Wraps the application once at the root layout level.
 */

'use client';

import { createContext, useContext, ReactNode } from 'react';
import { useWorkspaceRuntime } from './workspace-runtime';
import { useSelectionRuntime } from './selection-runtime';
import { useTimelineRuntime } from './timeline-runtime';
import { useNavigationRuntime } from './navigation-runtime';

export interface RuntimeContextValue {
  workspace: ReturnType<typeof useWorkspaceRuntime>;
  selection: ReturnType<typeof useSelectionRuntime>;
  timeline: ReturnType<typeof useTimelineRuntime>;
  navigation: ReturnType<typeof useNavigationRuntime>;
}

const RuntimeContext = createContext<RuntimeContextValue | null>(null);

interface RuntimeProviderProps {
  children: ReactNode;
}

export function RuntimeProvider({ children }: RuntimeProviderProps) {
  const workspace = useWorkspaceRuntime();
  const selection = useSelectionRuntime();
  const timeline = useTimelineRuntime();
  const navigation = useNavigationRuntime();

  return (
    <RuntimeContext.Provider value={{ workspace, selection, timeline, navigation }}>
      {children}
    </RuntimeContext.Provider>
  );
}

export function useRuntime(): RuntimeContextValue {
  const context = useContext(RuntimeContext);
  if (!context) {
    throw new Error('useRuntime must be used within RuntimeProvider');
  }
  return context;
}

// Convenience hooks
export function useWorkspace() {
  const { workspace } = useRuntime();
  return workspace;
}

export function useSelection() {
  const { selection } = useRuntime();
  return selection;
}

export function useTimeline() {
  const { timeline } = useRuntime();
  return timeline;
}

export function useNavigation() {
  const { navigation } = useRuntime();
  return navigation;
}
