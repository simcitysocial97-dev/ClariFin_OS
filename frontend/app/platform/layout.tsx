/**
 * Platform Console Layout — M9-C57 Phase 5 + Phase 9, hardened in M9-C71
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
 *     Enforced by the root layout's ShellBoundary, which skips the financial
 *     shell for /platform routes (M9-C71).
 *   - Dark theme by default (operational UI convention)
 *   - Platform sidebar navigation (added in Phase 9)
 *   - No financial data or controls
 *   - Self-contained providers: QueryProvider, ThemeProvider, TooltipProvider,
 *     ErrorBoundary, Toaster
 *
 * M9-C71: this layout used to declare a second <main> around children that the
 * providers had already wrapped in their own <main>. Exactly one content
 * landmark is declared now — here — and the providers only own the title bar.
 */

import type { ReactNode } from 'react';
import { PlatformConsoleProviders } from './platform-providers';
import { PlatformSidebar } from '@/components/platform/sidebar';
import { PlatformFooterBar } from '@/components/platform/footer-bar';
import { PlatformBackendStatus } from '@/components/platform/backend-status-bar';

/**
 * M11 — the backend status strip is part of the *shell*, not of any page.
 *
 * A cold-start operator lands on whichever route they last used. Per-page states
 * make the console's answer depend on the route, which is exactly the property
 * an operator cannot afford: "is the backend up?" must be answerable from any
 * console screen. It is driven by the fast liveness probe only, so it appears
 * even while a page's data reads are still outstanding.
 */
export const metadata = {
  title: 'Platform Console — ClariFin OS',
  description: 'ClariFin Platform Operations Console',
};

export default function PlatformLayout({ children }: { children: ReactNode }) {
  return (
    <PlatformConsoleProviders>
      <div className="flex min-h-0 flex-1 overflow-hidden">
        <PlatformSidebar />
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <PlatformBackendStatus />
          <main
            data-testid="platform-content"
            className="flex-1 overflow-auto p-5"
          >
            {children}
          </main>
          <PlatformFooterBar />
        </div>
      </div>
    </PlatformConsoleProviders>
  );
}
