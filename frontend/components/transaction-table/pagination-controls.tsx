/**
 * Pagination Controls Component - Stage 3 Transaction Intelligence Workspace
 *
 * Pagination controls for the transaction table.
 * Displays current page, total pages, and navigation buttons.
 * Dark mode support with bg-background classes.
 * Accessibility with proper ARIA attributes.
 */

'use client';

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface PaginationControlsProps {
  page: number;
  limit: number;
  total: number;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
}

/**
 * Pagination Controls Component
 * Displays pagination controls with page navigation and limit selection
 * Responsive design with proper spacing
 * Dark mode support with bg-background classes
 * Accessibility with ARIA labels
 */
export function PaginationControls({
  page,
  limit,
  total,
  onPageChange,
  onLimitChange,
}: PaginationControlsProps) {
  const totalPages = Math.ceil(total / limit);
  const startItem = (page - 1) * limit + 1;
  const endItem = Math.min(page * limit, total);

  const canPreviousPage = page > 1;
  const canNextPage = page < totalPages;

  const handlePreviousPage = () => {
    if (canPreviousPage) {
      onPageChange(page - 1);
    }
  };

  const handleNextPage = () => {
    if (canNextPage) {
      onPageChange(page + 1);
    }
  };

  const handleFirstPage = () => {
    onPageChange(1);
  };

  const handleLastPage = () => {
    onPageChange(totalPages);
  };

  const handleLimitChange = (value: string) => {
    onLimitChange(parseInt(value, 10));
  };

  if (total === 0) {
    return null;
  }

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 bg-background dark:bg-background border-t">
      {/* Items per page selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Items per page:</span>
        <Select value={String(limit)} onValueChange={handleLimitChange}>
          <SelectTrigger className="w-[70px]" aria-label="Select items per page">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="10">10</SelectItem>
            <SelectItem value="25">25</SelectItem>
            <SelectItem value="50">50</SelectItem>
            <SelectItem value="100">100</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Page info */}
      <div className="text-sm text-muted-foreground">
        Showing {startItem} to {endItem} of {total} transactions
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="sm"
          onClick={handleFirstPage}
          disabled={!canPreviousPage}
          aria-label="Go to first page"
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handlePreviousPage}
          disabled={!canPreviousPage}
          aria-label="Go to previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="px-3 text-sm font-medium" aria-label={`Page ${page} of ${totalPages}`}>
          {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={handleNextPage}
          disabled={!canNextPage}
          aria-label="Go to next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleLastPage}
          disabled={!canNextPage}
          aria-label="Go to last page"
        >
          <ChevronsRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}