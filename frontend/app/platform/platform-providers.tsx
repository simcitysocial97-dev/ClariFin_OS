/**
 * Platform Console Providers — M9-C57 Phase 5 / M9-C71
 *
 * Client-side providers for the Platform Console.
 * Separated from layout to avoid "use client" on the layout file
 * (which would prevent metadata export).
 *
 * M9-C71: this component owns the console's single top-level chrome
 * (title bar) and the single <main> landmark. `app/platform/layout.tsx` used to
 * render a *second* <main> around the same children, so every console page
 * shipped two main landmarks — an accessibility defect that also made
 * "which main is the page" ambiguous for assistive technology and for the E2E
 * contract. The title bar stays here, the sidebar stays in the layout, and the
 * content landmark is declared exactly once.
 */

'use client';

import type { ReactNode } from 'react';
import { QueryProvider } from '@/components/query-provider';
import { ThemeProvider } from '@/components/theme-provider';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { Toaster } from '@/components/ui/toaster';

interface PlatformConsoleProvidersProps {
  children: ReactNode;
}

export function PlatformConsoleProviders({ children }: PlatformConsoleProvidersProps) {
  return (
    <TooltipProvider delayDuration={300}>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem
        disableTransitionOnChange
      >
        <QueryProvider>
          <ErrorBoundary
            fallback={
              <div className="flex h-screen items-center justify-center text-[var(--text-tertiary)]">
                Platform Console unavailable
              </div>
            }
          >
            <Toaster />
            <div className="flex h-screen flex-col bg-[var(--surface-base)] text-[var(--text-primary)] overflow-hidden">
              {/* Title bar — distinct from the financial OS header */}
              <header
                data-testid="platform-title-bar"
                className="flex h-11 shrink-0 items-center gap-3 border-b border-[var(--border-subtle)] bg-[var(--surface-raised)] px-5">
                <span className="font-mono text-xs uppercase tracking-widest text-[var(--text-tertiary)]">
                  Platform
                </span>
                <span className="h-4 w-px bg-[var(--border-subtle)]" />
                <span className="text-sm font-semibold text-[var(--text-primary)]">
                  ClariFin OS
                </span>
                <span className="ml-auto font-mono text-xs text-[var(--text-tertiary)]">
                  v1.0.0
                </span>
              </header>

              {children}
            </div>
          </ErrorBoundary>
        </QueryProvider>
      </ThemeProvider>
    </TooltipProvider>
  );
}
