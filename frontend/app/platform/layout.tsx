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
  return (
    <PlatformConsoleProviders>
      <div className="flex flex-col h-screen bg-[var(--surface-base)] text-[var(--text-primary)] overflow-hidden">
        {/* Title bar — distinct from financial OS header */}
        <header className="flex items-center gap-3 px-5 h-11 border-b border-[var(--border-subtle)] bg-[var(--surface-raised)] shrink-0">
          <span className="text-xs font-mono text-[var(--text-tertiary)] uppercase tracking-widest">
            Platform
          </span>
          <span className="h-4 w-px bg-[var(--border-subtle)]" />
          <span className="text-sm font-semibold text-[var(--text-primary)]">
            ClariFin OS
          </span>
          <span className="ml-auto text-xs text-[var(--text-tertiary)] font-mono">
            v1.0.0
          </span>
        </header>

        {/* Main content — fills remaining viewport */}
        <main className="flex-1 overflow-auto p-5">
          {children}
        </main>
      </div>
    </PlatformConsoleProviders>
  );
}