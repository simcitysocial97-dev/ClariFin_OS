/**
 * Amount Filter Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for amount range filtering.
 */

'use client';

import { useState } from 'react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { IndianRupee } from 'lucide-react';
import type { AmountFilter } from '@/lib/filters/types';

interface AmountFilterProps {
  value: AmountFilter | null;
  onChange: (filter: AmountFilter | null) => void;
}

/**
 * Amount Filter Component
 * Allows users to set min/max amount for filtering transactions
 */
export function AmountFilter({ value, onChange }: AmountFilterProps) {
  const [minAmount, setMinAmount] = useState<string>(
    value?.min !== undefined ? String(value.min / 100) : ''
  );
  const [maxAmount, setMaxAmount] = useState<string>(
    value?.max !== undefined ? String(value.max / 100) : ''
  );

  const handleApply = () => {
    const min = minAmount ? Math.round(parseFloat(minAmount) * 100) : undefined;
    const max = maxAmount ? Math.round(parseFloat(maxAmount) * 100) : undefined;
    if (min !== undefined || max !== undefined) {
      onChange({ min, max });
    } else {
      onChange(null);
    }
  };

  const handleClear = () => {
    setMinAmount('');
    setMaxAmount('');
    onChange(null);
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="w-[140px] justify-start text-left font-normal">
          <IndianRupee className="mr-2 h-4 w-4" />
          Amount
          {value && ` (₹${value.min ? value.min / 100 : 0} - ₹${value.max ? value.max / 100 : '∞'})`}
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="w-full max-w-md">
        <div className="flex flex-col gap-4 p-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Min (₹)</label>
              <Input
                type="number"
                placeholder="0"
                value={minAmount}
                onChange={(e) => setMinAmount(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Max (₹)</label>
              <Input
                type="number"
                placeholder="No limit"
                value={maxAmount}
                onChange={(e) => setMaxAmount(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleApply} className="flex-1">
              Apply
            </Button>
            {value && (
              <Button variant="ghost" onClick={handleClear}>
                Clear
              </Button>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}