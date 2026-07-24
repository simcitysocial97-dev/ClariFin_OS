/**
 * Behaviour Empty State - Stage 4 Behaviour Intelligence Workspace
 *
 * Empty state components for behaviour workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Behaviour Empty State Props
 */
interface BehaviourEmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

/**
 * Behaviour Empty State Component
 */
export function BehaviourEmptyState({
  title = 'No behaviour data found',
  description = 'Try adjusting your filters or search query.',
  actionLabel = 'Clear filters',
  onAction,
}: BehaviourEmptyStateProps) {
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