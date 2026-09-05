/**
 * Platform Console Providers — M9-C57 Phase 5
 *
 * Client-side providers for the Platform Console.
 * Separated from layout to avoid "use client" on the layout file
 * (which would prevent metadata export).
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
          <ErrorBoundary fallback={<div className="flex items-center justify-center h-full text-[var(--text-tertiary)]">Platform Console unavailable</div>}>
            <Toaster />
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
          </ErrorBoundary>
        </QueryProvider>
      </ThemeProvider>
    </TooltipProvider>
  );
}