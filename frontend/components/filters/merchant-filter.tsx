/**
 * Merchant Filter Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for merchant filtering.
 */

'use client';

import { useState } from 'react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';

interface MerchantFilterProps {
  value: string[];
  onChange: (merchants: string[]) => void;
  availableMerchants?: string[];
}

/**
 * Merchant Filter Component
 * Allows users to select merchants for filtering transactions
 */
export function MerchantFilter({ value, onChange, availableMerchants = [] }: MerchantFilterProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMerchants, setSelectedMerchants] = useState<string[]>(value);

  const filteredMerchants = availableMerchants.filter(merchant =>
    merchant.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleMerchantToggle = (merchant: string) => {
    const newSelected = selectedMerchants.includes(merchant)
      ? selectedMerchants.filter(m => m !== merchant)
      : [...selectedMerchants, merchant];
    setSelectedMerchants(newSelected);
    onChange(newSelected);
  };

  const clearAll = () => {
    setSelectedMerchants([]);
    onChange([]);
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="w-[140px] justify-start text-left font-normal">
          <Search className="mr-2 h-4 w-4" />
          Merchant
          {value.length > 0 && ` (${value.length})`}
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="w-full max-w-md">
        <div className="flex flex-col gap-4 p-4">
          <Input
            placeholder="Search merchants..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <div className="max-h-60 overflow-y-auto">
            {filteredMerchants.map(merchant => (
              <div key={merchant} className="flex items-center space-x-2 py-1">
                <Checkbox
                  id={`merchant-${merchant}`}
                  checked={selectedMerchants.includes(merchant)}
                  onCheckedChange={() => handleMerchantToggle(merchant)}
                />
                <label htmlFor={`merchant-${merchant}`} className="text-sm">
                  {merchant}
                </label>
              </div>
            ))}
          </div>
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