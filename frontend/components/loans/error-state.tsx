/**
 * Loans Error State - Stage 4 Loans Intelligence Workspace
 *
 * Error state components for loans workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Loans Error State Props
 */
interface LoansErrorStateProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

/**
 * Loans Error State Component
 */
export function LoansErrorState({
  message,
  onRetry,
  className,
}: LoansErrorStateProps) {
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