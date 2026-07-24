/**
 * Net Worth Error State - Stage 4 Net Worth Intelligence Workspace
 *
 * Handles all error states for net worth workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, ChevronDown } from 'lucide-react';

/**
 * Net Worth Error State Props
 */
interface ErrorStateProps {
  error: Error | null;
  onRetry: () => void;
}

/**
 * Net Worth Error State Component
 */
export function ErrorState({ error, onRetry }: ErrorStateProps) {
  if (!error) return null;

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">Something went wrong</h3>
      <p className="text-sm text-gray-500 mb-4 max-w-md">
        {error.message || 'Failed to load net worth data. Please try again.'}
      </p>
      <div className="flex gap-2">
        <Button onClick={onRetry} variant="default">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
        <Button variant="outline">
          <ChevronDown className="h-4 w-4 mr-2" />
          Show details
        </Button>
      </div>
    </div>
  );
}