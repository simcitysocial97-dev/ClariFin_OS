/**
 * Reconciliation Error State - Stage 4 Reconciliation Intelligence Workspace
 *
 * Error state components for reconciliation workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Reconciliation Error State Props
 */
interface ReconciliationErrorStateProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

/**
 * Reconciliation Error State Component
 */
export function ReconciliationErrorState({
  message,
  onRetry,
  className,
}: ReconciliationErrorStateProps) {
  return (
    <Alert variant="destructive" role="alert" className={cn('bg-background dark:bg-background', className)}>
      <AlertCircle className="h-4 w-4" />
      {/* AlertTitle renders an h5, which is correct for a label inside an alert
          but skips h1-h4. When this component is the *whole* page — as it is
          whenever the reconciliation API is unavailable — the page then has no
          h1/h2/h3 at all, so a screen-reader user gets no page heading and the
          reconciliation "should display page title" E2E assertion fails on any
          checkout without that API. The empty state already carries an h3; this
          state now matches it. AlertTitle is left alone so its other three
          call sites are unaffected. */}
      <h3 className="mb-1 font-medium leading-none tracking-tight">Error</h3>
      <AlertDescription>
        {message}
        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="ml-4"
          >
            Retry
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}