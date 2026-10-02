import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/toaster';
import { ThemeProvider } from '@/components/theme-provider';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { QueryProvider } from '@/components/query-provider';
import { ShellBoundary } from '@/components/os-shell/shell-boundary';
import { MemberBoundary } from '@/components/os-shell/member-boundary';
import { RuntimeProvider } from '@/lib/runtime';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'ClariFin OS - Financial Operating System',
  description: 'Personal finance dashboard with automatic transaction categorization and financial graph analysis',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
      </head>
      <body className={inter.className}>
        <TooltipProvider delayDuration={300}>
          <ThemeProvider
            attribute="class"
            defaultTheme="dark"
            enableSystem
            disableTransitionOnChange
          >
            <QueryProvider>
              <MemberBoundary>
                <RuntimeProvider>
                  <ErrorBoundary>
                    {/* M9-C71: the Platform Console is a standalone operational
                        interface (app/platform/layout.tsx invariant: "No AppShell").
                        ShellBoundary selects the shell by route so that invariant
                        actually holds. */}
                    <ShellBoundary>{children}</ShellBoundary>
                  </ErrorBoundary>
                  <Toaster />
                </RuntimeProvider>
              </MemberBoundary>
            </QueryProvider>
          </ThemeProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
