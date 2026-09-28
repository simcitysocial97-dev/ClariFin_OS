'use client'

import React from 'react'
import { AlertTriangle } from 'lucide-react'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  componentName?: string
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to console in development
    console.error(
      `[ErrorBoundary] ${this.props.componentName ?? 'Component'} crashed:`,
      error,
      errorInfo
    )
    // In production: send to Sentry/GlitchTip here
    // Sentry.captureException(error, { extra: errorInfo })
  }

  override render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex flex-col items-center justify-center p-6 rounded-lg border border-destructive/20 bg-destructive/5 text-center gap-2">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <p className="text-sm font-medium text-destructive">
            {this.props.componentName
              ? `${this.props.componentName} failed to load`
              : 'This section failed to load'}
          </p>
          <p className="text-xs text-muted-foreground">
            Refresh the page or contact support if this persists
          </p>
        </div>
      )
    }

    return this.props.children
  }
}

/**
 * Error fallback component for use with React's error boundary conventions
 */
export function ErrorFallback({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) {
  return (
    <div className="flex items-center justify-center min-h-[400px] p-6">
      <div className="text-center">
        <p className="text-sm text-muted-foreground">
          {error.message || 'An unexpected error occurred. Please try again.'}
        </p>
        <button onClick={resetErrorBoundary} className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md">
          Try Again
        </button>
      </div>
    </div>
  );
}
