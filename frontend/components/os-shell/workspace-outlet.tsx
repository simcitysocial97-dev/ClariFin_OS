/**
 * Workspace Outlet - Stage 8A Financial Operating System Shell
 *
 * Next.js dynamic route outlet for workspace pages.
 * Renders workspace content based on current route.
 * No business logic - pure routing.
 */

'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

// ===== Workspace Outlet Component =====
interface WorkspaceOutletProps {
  children: ReactNode;
  className?: string;
}

export function WorkspaceOutlet({ children, className }: WorkspaceOutletProps) {
  return (
    <div className={cn('h-full w-full', className)}>
      {/* Workspace content is rendered by Next.js routing */}
      {children}
    </div>
  );
}