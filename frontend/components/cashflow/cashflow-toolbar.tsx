/**
 * Cashflow Toolbar - Stage 4 Cashflow Truth Workspace
 *
 * Toolbar for cashflow workspace actions.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Button } from '@/components/ui/button';
import { RefreshCw, Download, Share2, FileText } from 'lucide-react';
import { CashflowSearch } from './cashflow-search';

/**
 * Cashflow Toolbar Props
 */
interface CashflowToolbarProps {
  onRefresh: () => void;
  onExport: () => void;
  onShare: () => void;
  onShowEvidence: () => void;
  onSearch: (query: string) => void;
  onClearSearch: () => void;
}

/**
 * Cashflow Toolbar Component
 *
 * Provides action buttons and search for the cashflow workspace.
 */
export function CashflowToolbar({
  onRefresh,
  onExport,
  onShare,
  onShowEvidence,
  onSearch,
  onClearSearch,
}: CashflowToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between p-4 border-b">
      {/* Search */}
      <CashflowSearch onSearch={onSearch} onClear={onClearSearch} />

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onShowEvidence}
          aria-label="Show evidence"
        >
          <FileText className="h-4 w-4 mr-1" />
          Evidence
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onShare}
          aria-label="Share"
        >
          <Share2 className="h-4 w-4 mr-1" />
          Share
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onExport}
          aria-label="Export"
        >
          <Download className="h-4 w-4 mr-1" />
          Export
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          aria-label="Refresh"
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          Refresh
        </Button>
      </div>
    </div>
  );
}