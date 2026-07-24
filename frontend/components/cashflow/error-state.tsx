/**
 * Error State - Stage 4 Cashflow Truth Workspace
 *
 * Error state component for cashflow workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

/**
 * Error State Props
 */
interface ErrorStateProps {
  error: Error | null;
  onRetry: () => void;
}

/**
 * Error State Component
 *
 * Shows error message with retry option.
 */
export function CashflowErrorState({ error, onRetry }: ErrorStateProps) {
  if (!error) {
    return null;
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex flex-col items-center gap-4 text-center">
          <AlertCircle className="h-12 w-12 text-red-500" />
          <div>
            <h3 className="font-semibold text-lg">Something went wrong</h3>
            <p className="text-sm text-gray-500 mt-1">{error.message}</p>
          </div>
          <Button onClick={onRetry} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}