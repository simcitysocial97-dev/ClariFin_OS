/**
 * Empty State Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for empty state display.
 */

import { EmptyState as UiEmptyState } from '@/components/ui/empty-state';
import { FileText } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

/**
 * Empty State Component
 * Displays message when no transactions are found
 */
export function EmptyState({
  title = 'No transactions found',
  description = 'Try adjusting your filters or search query.',
  actionLabel = 'Clear filters',
  onAction,
}: EmptyStateProps) {
  return (
    <UiEmptyState
      icon={<FileText className="h-10 w-10" />}
      title={title}
      description={description}
      action={onAction ? { label: actionLabel, onClick: onAction } : undefined}
    />
  );
}