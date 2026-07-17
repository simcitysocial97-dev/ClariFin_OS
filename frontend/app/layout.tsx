import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { MainLayout } from '@/components/layout/main-layout'
import { Toaster } from '@/components/ui/toaster'
import { ThemeProvider } from '@/components/theme-provider'
import { MemberProvider } from '@/lib/context/member-context'
import { ErrorBoundary } from '@/components/error-boundary'
import { QueryProvider } from '@/components/query-provider'
import { ExplainabilityProvider } from '@/components/explainability/providers/ExplainabilityProvider'
import { ExplainabilityDrawer } from '@/components/explainability'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'FinTrack - Bank Statement Parser',
  description: 'Personal finance dashboard with automatic transaction categorization',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Load PDF.js from CDN */}
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if (typeof pdfjsLib !== 'undefined') {
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
              }
            `,
          }}
        />
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
              <ExplainabilityProvider>
                <ErrorBoundary>
                  <MainLayout>{children}</MainLayout>
                </ErrorBoundary>
                <Toaster />
                <ExplainabilityDrawer />
              </ExplainabilityProvider>
            </MemberProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}