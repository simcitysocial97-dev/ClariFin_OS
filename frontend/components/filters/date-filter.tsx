/**
 * Date Filter Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for date range filtering.
 */

'use client';

import { useState } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';
import type { DateFilter } from '@/lib/filters/types';

interface DateFilterProps {
  value: DateFilter | null;
  onChange: (filter: DateFilter | null) => void;
}

/**
 * Date Filter Component
 * Allows users to select a date range for filtering transactions
 */
export function DateFilter({ value, onChange }: DateFilterProps) {
  const [fromDate, setFromDate] = useState<Date | undefined>(
    value?.from ? new Date(value.from) : undefined
  );
  const [toDate, setToDate] = useState<Date | undefined>(
    value?.to ? new Date(value.to) : undefined
  );

  const handleFromDateSelect = (date: Date | undefined) => {
    setFromDate(date);
    if (date) {
      onChange({
        from: format(date, 'yyyy-MM-dd'),
        to: toDate ? format(toDate, 'yyyy-MM-dd') : undefined,
      });
    } else if (toDate) {
      onChange({
        from: undefined,
        to: format(toDate, 'yyyy-MM-dd'),
      });
    } else {
      onChange(null);
    }
  };

  const handleToDateSelect = (date: Date | undefined) => {
    setToDate(date);
    if (date) {
      onChange({
        from: fromDate ? format(fromDate, 'yyyy-MM-dd') : undefined,
        to: format(date, 'yyyy-MM-dd'),
      });
    } else if (fromDate) {
      onChange({
        from: format(fromDate, 'yyyy-MM-dd'),
        to: undefined,
      });
    } else {
      onChange(null);
    }
  };

  const clearFilter = () => {
    setFromDate(undefined);
    setToDate(undefined);
    onChange(null);
  };

  return (
    <div className="flex items-center gap-2">
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="outline" className="w-[140px] justify-start text-left font-normal">
            <CalendarIcon className="mr-2 h-4 w-4" />
            {fromDate ? format(fromDate, 'PPP') : 'From date'}
          </Button>
        </SheetTrigger>
        <SheetContent side="bottom" className="w-auto p-0">
          <Calendar
            mode="single"
            selected={fromDate}
            onSelect={handleFromDateSelect}
            initialFocus
          />
        </SheetContent>
      </Sheet>

      <Sheet>
        <SheetTrigger asChild>
          <Button variant="outline" className="w-[140px] justify-start text-left font-normal">
            <CalendarIcon className="mr-2 h-4 w-4" />
            {toDate ? format(toDate, 'PPP') : 'To date'}
          </Button>
        </SheetTrigger>
        <SheetContent side="bottom" className="w-auto p-0">
          <Calendar
            mode="single"
            selected={toDate}
            onSelect={handleToDateSelect}
            initialFocus
          />
        </SheetContent>
      </Sheet>

      {value && (
        <Button variant="ghost" size="sm" onClick={clearFilter}>
          Clear
        </Button>
      )}
    </div>
  );
}
