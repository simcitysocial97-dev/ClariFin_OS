/**
 * Reconciliation Error State - Stage 4 Reconciliation Intelligence Workspace
 *
 * Error state components for reconciliation workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
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
      <AlertTitle>Error</AlertTitle>
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