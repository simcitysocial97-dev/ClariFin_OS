/**
 * Platform Console Layout — M9-C57 Phase 5
 *
 * Standalone layout for the /platform route group.
 *
 * This layout is intentionally separate from the financial AppShell.
 * The Platform Console is a distinct operational interface — not a
 * workspace within the financial OS. It uses its own shell, color
 * palette, and navigation so that operators can clearly distinguish
 * between "inspecting ClariFin_OS" and "using ClariFin_OS".
 *
 * Invariants:
 *   - No AppShell (no left-rail, no top-command-bar, no workspace host)
 *   - Dark theme by default (operational UI convention)
 *   - Minimal chrome: title bar + outlet only
 *   - No financial data or controls
 *   - Self-contained providers: QueryProvider, ThemeProvider, TooltipProvider,
 *     ErrorBoundary, Toaster
 */

import type { ReactNode } from 'react';
import { PlatformConsoleProviders } from './platform-providers';

export const metadata = {
  title: 'Platform Console — ClariFin OS',
  description: 'ClariFin Platform Operations Console',
};

export default function PlatformLayout({ children }: { children: ReactNode }) {
  return <PlatformConsoleProviders>{children}</PlatformConsoleProviders>;
}