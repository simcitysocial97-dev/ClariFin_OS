/**
 * Workspace Provider - Stage 7.5 Runtime Consolidation
 *
 * React provider component for workspace context.
 */

'use client';

import { ReactNode } from 'react';
import { WorkspaceContext, useWorkspaceContext } from './workspace-context';

interface WorkspaceProviderProps {
  children: ReactNode;
}

export function WorkspaceProvider({ children }: WorkspaceProviderProps) {
  const value = useWorkspaceContext();

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}