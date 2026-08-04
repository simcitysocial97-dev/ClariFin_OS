/**
 * Deep Link Sync - Stage 8B Navigation Experience
 *
 * Synchronizes the Next.js router with the NavigationRuntime.
 * On mount, reads the current URL and pushes it to navigation history.
 * Listens for popstate (browser back/forward) and updates runtime state.
 * Does NOT modify frozen runtimes — only reads from and writes to them.
 */

'use client';

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { navigationRuntime } from '@/lib/runtime';
import type { WorkspaceName } from '@/lib/workspace/workspace-context';

// Map URL paths to workspace names
const PATH_TO_WORKSPACE: Record<string, WorkspaceName> = {
  '/dashboard': 'dashboard',
  '/transactions': 'transactions',
  '/accounts': 'accounts',
  '/cards': 'cards',
  '/loans': 'loans',
  '/investments': 'investments',
  '/net-worth': 'net-worth',
  '/cashflow': 'cashflow',
  '/behaviour': 'behaviour',
  '/forecast': 'forecast',
  '/reconciliation': 'reconciliation',
  '/settings': 'settings',
};

function getWorkspaceFromPath(path: string): WorkspaceName | null {
  const cleanPath = path.split('?')[0];
  return PATH_TO_WORKSPACE[cleanPath] ?? null;
}

export function DeepLinkSync() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;

    const fullPath = pathname + (searchParams.toString() ? `?${searchParams.toString()}` : '');
    const workspace = getWorkspaceFromPath(fullPath);

    if (workspace) {
      // Push to navigation history (avoid duplicate on initial load)
      const currentState = navigationRuntime.state;
      const lastEntry = currentState.history[currentState.currentIndex];
      if (!lastEntry || lastEntry.path !== fullPath) {
        navigationRuntime.pushPath(fullPath, workspace);
      }
    }
  }, [pathname, searchParams]);

  // Listen for browser back/forward
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handlePopState = () => {
      const currentPath = window.location.pathname + window.location.search;
      const workspace = getWorkspaceFromPath(currentPath);
      if (workspace) {
        navigationRuntime.pushPath(currentPath, workspace);
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Null element — this is a side-effect-only component
  return null;
}
