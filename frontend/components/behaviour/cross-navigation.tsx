/**
 * Behaviour Cross Navigation - Stage 4 Behaviour Intelligence Workspace
 *
 * Cross-navigation links to related workspaces.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { Link } from 'lucide-react';

/**
 * Behaviour Cross Navigation Props
 */
interface CrossNavigationProps {
  crossReferences?: {
    cashflow?: string;
    netWorth?: string;
  };
}

/**
 * Behaviour Cross Navigation Component
 */
export function CrossNavigation({ crossReferences }: CrossNavigationProps) {
  if (!crossReferences) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 pt-4 border-t">
      <span className="text-sm text-gray-500">Related:</span>
      {crossReferences.cashflow && (
        <Button variant="link" size="sm" asChild>
          <a href={crossReferences.cashflow}>
            <Link className="h-3 w-3 mr-1" />
            Cashflow
          </a>
        </Button>
      )}
      {crossReferences.netWorth && (
        <Button variant="link" size="sm" asChild>
          <a href={crossReferences.netWorth}>
            <Link className="h-3 w-3 mr-1" />
            Net Worth
          </a>
        </Button>
      )}
    </div>
  );
}