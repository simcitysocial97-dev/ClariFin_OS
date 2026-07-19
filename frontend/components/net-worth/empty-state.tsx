/**
 * Net Worth Empty State - Stage 4 Net Worth Intelligence Workspace
 *
 * Handles empty states for net worth workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Plus, Wallet } from 'lucide-react';

/**
 * Net Worth Empty State Props
 */
interface EmptyStateProps {
  onAddAccounts: () => void;
}

/**
 * Net Worth Empty State Component
 */
export function EmptyState({ onAddAccounts }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <Wallet className="h-12 w-12 text-gray-400 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">No accounts configured</h3>
      <p className="text-sm text-gray-500 mb-4 max-w-md">
        Add accounts and investments to start tracking your net worth.
      </p>
      <Button onClick={onAddAccounts}>
        <Plus className="h-4 w-4 mr-2" />
        Add Accounts
      </Button>
    </div>
  );
}