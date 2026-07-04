'use client';

import { Component, ReactNode } from 'react';
import { AlertCircle, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  showDetails: boolean;
}

/**
 * Global Error Boundary
 * Catches JavaScript errors anywhere in the child component tree
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null, showDetails: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error, errorInfo: null, showDetails: false };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null, showDetails: false });
  };

  toggleDetails = (): void => {
    this.setState(prev => ({ showDetails: !prev.showDetails }));
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isDev = process.env.NODE_ENV === 'development';
      const { error, errorInfo, showDetails } = this.state;

      return (
        <div className="flex items-center justify-center min-h-[400px] p-6">
          <Card className="w-full max-w-2xl border-destructive/50">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-destructive/10 flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-destructive" />
              </div>
              <CardTitle className="text-xl">Something went wrong</CardTitle>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <p className="text-sm text-muted-foreground">
                An unexpected error occurred. Please try again.
              </p>
              
              {/* Always show error message */}
              {error && (
                <div className="text-sm text-destructive bg-destructive/5 p-3 rounded-md">
                  {error.message}
                </div>
              )}

              {/* Development mode: show full stack trace */}
              {isDev && error && (
                <div className="text-left">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={this.toggleDetails}
                    className="mb-2"
                  >
                    {showDetails ? (
                      <ChevronUp className="h-4 w-4 mr-2" />
                    ) : (
                      <ChevronDown className="h-4 w-4 mr-2" />
                    )}
                    {showDetails ? 'Hide Details' : 'Show Details'}
                  </Button>
                  
                  {showDetails && (
                    <div className="space-y-3">
                      <details className="text-xs bg-muted p-3 rounded-md overflow-auto max-h-[200px]" open>
                        <summary className="font-semibold mb-2 cursor-pointer">Error Stack</summary>
                        <pre className="whitespace-pre-wrap break-all text-destructive">
                          {error.stack}
                        </pre>
                      </details>
                      
                      {errorInfo && (
                        <details className="text-xs bg-muted p-3 rounded-md overflow-auto max-h-[200px]" open>
                          <summary className="font-semibold mb-2 cursor-pointer">Component Stack</summary>
                          <pre className="whitespace-pre-wrap break-all">
                            {errorInfo.componentStack}
                          </pre>
                        </details>
                      )}
                    </div>
                  )}
                </div>
              )}

              <Button onClick={this.handleReset} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Error fallback component for use with React's error boundary conventions
 */
export function ErrorFallback({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) {
  const isDev = process.env.NODE_ENV === 'development';
  
  return (
    <div className="flex items-center justify-center min-h-[400px] p-6">
      <Card className="w-full max-w-md border-destructive/50">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <CardTitle className="text-xl">Something went wrong</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <p className="text-sm text-muted-foreground">
            {error.message || 'An unexpected error occurred. Please try again.'}
          </p>
          
          {isDev && error.stack && (
            <details className="text-left">
              <summary className="text-xs text-muted-foreground cursor-pointer">Stack Trace</summary>
              <pre className="text-xs text-left bg-muted p-3 rounded-md overflow-auto max-h-[200px] mt-2">
                {error.stack}
              </pre>
            </details>
          )}
          
          <Button onClick={resetErrorBoundary} className="w-full">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
