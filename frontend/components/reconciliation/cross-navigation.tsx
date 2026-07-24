/**
 * Reconciliation Cross Navigation - Stage 4 Reconciliation Intelligence Workspace
 *
 * Cross-navigation links to related workspaces.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Link } from 'lucide-react';

/**
 * Reconciliation Cross Navigation Props
 */
interface CrossNavigationProps {
  crossReferences?: {
    accounts?: string;
    transactions?: string;
  };
}

/**
 * Reconciliation Cross Navigation Component
 */
export function CrossNavigation({ crossReferences }: CrossNavigationProps) {
  if (!crossReferences) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 pt-4 border-t">
      <span className="text-sm text-gray-500">Related:</span>
      {crossReferences.accounts && (
        <Button variant="link" size="sm" asChild>
          <a href={crossReferences.accounts}>
            <Link className="h-3 w-3 mr-1" />
            Accounts
          </a>
        </Button>
      )}
      {crossReferences.transactions && (
        <Button variant="link" size="sm" asChild>
          <a href={crossReferences.transactions}>
            <Link className="h-3 w-3 mr-1" />
            Transactions
          </a>
        </Button>
      )}
    </div>
  );
}