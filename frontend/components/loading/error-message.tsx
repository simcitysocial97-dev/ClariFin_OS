/**
 * Error Message Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for error state display.
 */

import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

/**
 * Error Message Component
 * Displays error message with optional retry button
 */
export function ErrorMessage({
  title = 'Error',
  message,
  onRetry,
  className,
}: ErrorMessageProps) {
  return (
    <Alert variant="destructive" role="alert" className={cn('bg-background dark:bg-background', className)}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
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
