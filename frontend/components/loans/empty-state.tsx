/**
 * Loans Empty State - Stage 4 Loans Intelligence Workspace
 *
 * Empty state components for loans workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Loans Empty State Props
 */
interface LoansEmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

/**
 * Loans Empty State Component
 */
export function LoansEmptyState({
  title = 'No loans found',
  description = 'Try adjusting your filters or search query.',
  actionLabel = 'Clear filters',
  onAction,
}: LoansEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <FileText className="h-10 w-10 text-gray-300 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 mb-4">{description}</p>
      {onAction && (
        <Button variant="outline" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}