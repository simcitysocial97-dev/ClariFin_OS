/**
 * Workspace Container - Stage 8A Financial Operating System Shell
 *
 * Pure container for workspace content.
 * Never contains logic.
 * Depending on workspace, hosts: Graph, Table, Matrix, Heatmap, Timeline, Charts, Forms, Investigation, Simulation.
 */

'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

// ===== Workspace Container Component =====
interface WorkspaceContainerProps {
  children: ReactNode;
  className?: string;
}

export function WorkspaceContainer({ children, className }: WorkspaceContainerProps) {
  return (
    <div
      className={cn(
        'absolute inset-0',
        'pt-44', // Account for top command bar (44px)
        'pl-180', // Account for left rail (180px)
        'pb-88', // Account for bottom timeline (88px)
        className,
      )}
    >
      <div className="h-full w-full overflow-hidden">
        {children}
      </div>
    </div>
  );
}