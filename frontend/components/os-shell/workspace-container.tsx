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
        'pt-11', // Account for top command bar (44px) - base
        'lg:pt-44', // Desktop: full top padding
        'pl-0', // Mobile: no left padding (sidebar hidden)
        'sm:pl-14', // Small: collapsed sidebar (56px)
        'lg:pl-[180px]', // Large: expanded sidebar (180px)
        'pr-0', // Mobile: no right padding (inspector hidden)
        'md:pr-[320px]', // Medium+: account for right inspector (320px)
        'pb-0', // Mobile: no bottom padding (timeline hidden)
        'md:pb-[88px]', // Medium+: timeline height (88px)
        className,
      )}
    >
      <div className="h-full w-full overflow-hidden">
        {children}
      </div>
    </div>
  );
}