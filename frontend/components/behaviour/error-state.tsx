/**
 * Behaviour Error State - Stage 4 Behaviour Intelligence Workspace
 *
 * Error state components for behaviour workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Behaviour Error State Props
 */
interface BehaviourErrorStateProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

/**
 * Behaviour Error State Component
 */
export function BehaviourErrorState({
  message,
  onRetry,
  className,
}: BehaviourErrorStateProps) {
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