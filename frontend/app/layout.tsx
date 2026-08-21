import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/toaster';
import { ThemeProvider } from '@/components/theme-provider';
import { TooltipProvider } from '@/components/ui/tooltip';
import { MemberProvider } from '@/lib/context/member-context';
import { ErrorBoundary } from '@/components/error-boundary';
import { QueryProvider } from '@/components/query-provider';
import { AppShell } from '@/components/os-shell';
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
              <MemberProvider>
                <RuntimeProvider>
                  <ErrorBoundary>
                    <AppShell>{children}</AppShell>
                  </ErrorBoundary>
                  <Toaster />
                </RuntimeProvider>
              </MemberProvider>
            </QueryProvider>
          </ThemeProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
