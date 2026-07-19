/**
 * Empty State - Stage 4 Cashflow Truth Workspace
 *
 * Empty state component for cashflow workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Plus } from 'lucide-react';

/**
 * Empty State Props
 */
interface EmptyStateProps {
  onAddData?: () => void;
}

/**
 * Empty State Component
 *
 * Shows empty state when no cashflow data is available.
 */
export function CashflowEmptyState({ onAddData }: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="p-12">
        <div className="flex flex-col items-center gap-4 text-center">
          <FileText className="h-12 w-12 text-gray-400" />
          <div>
            <h3 className="font-semibold text-lg">No cashflow data yet</h3>
            <p className="text-sm text-gray-500 mt-1">
              Add transactions to see your cashflow analysis
            </p>
          </div>
          {onAddData && (
            <Button onClick={onAddData} size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Transactions
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}