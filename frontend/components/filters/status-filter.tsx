/**
 * Status Filter Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for transaction status filtering.
 */

'use client';

import { useState } from 'react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Filter } from 'lucide-react';
import type { TransactionStatus } from '@/lib/filters/types';

interface StatusFilterProps {
  value: TransactionStatus[];
  onChange: (statuses: TransactionStatus[]) => void;
}

const STATUS_OPTIONS: TransactionStatus[] = ['cleared', 'pending', 'adjusted', 'rejected'];

/**
 * Status Filter Component
 * Allows users to select transaction statuses for filtering
 */
export function StatusFilter({ value, onChange }: StatusFilterProps) {
  const [selectedStatuses, setSelectedStatuses] = useState<TransactionStatus[]>(value);

  const handleStatusToggle = (status: TransactionStatus) => {
    const newSelected = selectedStatuses.includes(status)
      ? selectedStatuses.filter(s => s !== status)
      : [...selectedStatuses, status];
    setSelectedStatuses(newSelected);
    onChange(newSelected);
  };

  const clearAll = () => {
    setSelectedStatuses([]);
    onChange([]);
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="w-[140px] justify-start text-left font-normal">
          <Filter className="mr-2 h-4 w-4" />
          Status
          {value.length > 0 && ` (${value.length})`}
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="w-full max-w-md">
        <div className="flex flex-col gap-4 p-4">
          {STATUS_OPTIONS.map(status => (
            <div key={status} className="flex items-center space-x-2 py-1">
              <Checkbox
                id={`status-${status}`}
                checked={selectedStatuses.includes(status)}
                onCheckedChange={() => handleStatusToggle(status)}
              />
              <label htmlFor={`status-${status}`} className="text-sm capitalize">
                {status}
              </label>
            </div>
          ))}
          {value.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearAll}>
              Clear All
            </Button>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}