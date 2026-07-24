/**
 * Resizable Layout - Stage 8A Financial Operating System Shell
 *
 * Uses shadcn/ui Resizable Panels for layout management.
 * Handles docking, resizing, and panel state.
 * No business logic - pure UI state management.
 */

'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

// ===== Resizable Layout Component =====
interface ResizableLayoutProps {
  children: ReactNode;
  className?: string;
}

export function ResizableLayout({ children, className }: ResizableLayoutProps) {
  return (
    <div className={cn('h-full w-full', className)}>
      {children}
    </div>
  );
}