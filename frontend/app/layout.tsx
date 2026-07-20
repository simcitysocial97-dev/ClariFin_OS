import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/toaster';
import { ThemeProvider } from '@/components/theme-provider';
import { MemberProvider } from '@/lib/context/member-context';
import { ErrorBoundary } from '@/components/error-boundary';
import { QueryProvider } from '@/components/query-provider';
import { AppShell } from '@/components/os-shell';

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
        {/* Load PDF.js from CDN */}
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
        <script dangerouslySetInnerHTML={{
          __html: `
            if (typeof pdfjsLib !== 'undefined') {
              pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            }
          `
        }} />
        {/* Load Bank Parser */}
        <script src="/parser/browser-parser.js" defer />
        {/* Load Debug Panel */}
        <script src="/parser/debug.js" defer />
      </head>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <MemberProvider>
              <ErrorBoundary>
                <AppShell>{children}</AppShell>
              </ErrorBoundary>
              <Toaster />
            </MemberProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
