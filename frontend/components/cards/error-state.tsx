/**
 * Credit Cards Error State - Stage 4 Credit Cards Intelligence Workspace
 *
 * Error state components for credit cards workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Credit Cards Error State Props
 */
interface CreditCardsErrorStateProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

/**
 * Credit Cards Error State Component
 */
export function CreditCardsErrorState({
  message,
  onRetry,
  className,
}: CreditCardsErrorStateProps) {
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