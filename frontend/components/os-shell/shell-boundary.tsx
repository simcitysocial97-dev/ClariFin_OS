/**
 * Shell Boundary — M9-C71
 *
 * The financial workspace shell and the Platform Console are two different
 * applications that happen to share one Next.js root layout:
 *
 *   - the financial OS is a workspace inside a left-rail / command-bar shell
 *     with financial navigation, search, and a runtime status bar;
 *   - the Platform Console is a standalone operational interface. Its own
 *     layout (`app/platform/layout.tsx`) documents the invariant explicitly:
 *
 *         Invariants:
 *           - No AppShell (no left-rail, no top-command-bar, no workspace host)
 *           - Dark theme by default (operational UI convention)
 *           - Platform sidebar navigation
 *           - No financial data or controls
 *
 * That invariant was being violated: `app/layout.tsx` wrapped *every* route in
 * <AppShell>, so the operations console rendered inside the financial chrome —
 * two sidebars, two command bars, two <main> landmarks, and the financial
 * navigation available from an operator screen. It also multiplied the failed
 * API calls the financial shell issues, which is what kept the platform pages
 * from ever reaching a settled network state.
 *
 * A route group cannot fix this: in the App Router the root layout always wraps
 * every route beneath it. The shell therefore has to be selected by route, and
 * that decision is made here, in one place, as a single auditable rule.
 *
 * If a second standalone console is ever added, extend PLATFORM_PREFIXES rather
 * than reintroducing per-page special cases.
 */

'use client';

import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { AppShell } from '@/components/os-shell';

/** Route prefixes owned by the Platform Console, not the financial workspace. */
const PLATFORM_PREFIXES = ['/platform'] as const;

export function isStandaloneConsoleRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  const normalized = pathname.replace(/\/+$/, '') || '/';
  return PLATFORM_PREFIXES.some(
    (prefix) => normalized === prefix || normalized.startsWith(`${prefix}/`),
  );
}

/**
 * Renders children inside the financial workspace shell, except on the routes
 * that declare themselves standalone consoles.
 */
export function ShellBoundary({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  if (isStandaloneConsoleRoute(pathname)) {
    return <>{children}</>;
  }

  return <AppShell>{children}</AppShell>;
}
