/**
 * Category Filter Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for category filtering.
 */

'use client';

import { useState } from 'react';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';

interface CategoryFilterProps {
  value: string[];
  onChange: (categories: string[]) => void;
  availableCategories?: string[];
}

/**
 * Category Filter Component
 * Allows users to select categories for filtering transactions
 */
export function CategoryFilter({ value, onChange, availableCategories = [] }: CategoryFilterProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>(value);

  const filteredCategories = availableCategories.filter(cat =>
    cat.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCategoryToggle = (category: string) => {
    const newSelected = selectedCategories.includes(category)
      ? selectedCategories.filter(c => c !== category)
      : [...selectedCategories, category];
    setSelectedCategories(newSelected);
    onChange(newSelected);
  };

  const clearAll = () => {
    setSelectedCategories([]);
    onChange([]);
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="w-[140px] justify-start text-left font-normal">
          <Search className="mr-2 h-4 w-4" />
          Category
          {value.length > 0 && ` (${value.length})`}
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="w-full max-w-md">
        <div className="flex flex-col gap-4 p-4">
          <Input
            placeholder="Search categories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <div className="max-h-60 overflow-y-auto">
            {filteredCategories.map(category => (
              <div key={category} className="flex items-center space-x-2 py-1">
                <Checkbox
                  id={`cat-${category}`}
                  checked={selectedCategories.includes(category)}
                  onCheckedChange={() => handleCategoryToggle(category)}
                />
                <label htmlFor={`cat-${category}`} className="text-sm">
                  {category}
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