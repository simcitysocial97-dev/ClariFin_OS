/**
 * Investments Empty State - Stage 4 Investments Intelligence Workspace
 *
 * Empty state components for investments workspace.
 *
 * M11: the default action was "Clear filters". When the portfolio is empty
 * because nothing has been recorded, filters are not the reason and clearing
 * them cannot change anything — the state gave no way to add the first
 * holding. `onAdd` is offered when supplied.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { FileText, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Investments Empty State Props
 */
interface InvestmentsEmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  /** Offer the create action. Omitted where adding is not available. */
  onAdd?: () => void;
  /** True when filters are actually applied, so clearing them is meaningful. */
  hasActiveFilters?: boolean;
}

/**
 * Investments Empty State Component
 */
export function InvestmentsEmptyState({
  title = 'No investments found',
  description,
  actionLabel = 'Clear filters',
  onAction,
  onAdd,
  hasActiveFilters = false,
}: InvestmentsEmptyStateProps) {
  const resolvedDescription =
    description ??
    (hasActiveFilters
      ? 'No investment matches the current filters.'
      : 'No investments have been recorded yet. Add one to see portfolio value, allocation and returns.');

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <FileText className="h-10 w-10 text-gray-300 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 mb-4">{resolvedDescription}</p>
      <div className="flex items-center gap-2">
        {onAdd && (
          <Button size="sm" onClick={onAdd} data-testid="investments-empty-add">
            <Plus className="h-4 w-4 mr-1" />
            Add investment
          </Button>
        )}
        {onAction && hasActiveFilters && (
          <Button variant="outline" size="sm" onClick={onAction} data-testid="investments-empty-clear-filters">
            {actionLabel}
          </Button>
        )}
      </div>
    </div>
  );
}