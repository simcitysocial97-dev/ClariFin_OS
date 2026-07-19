/**
 * Cashflow Search - Stage 4 Cashflow Truth Workspace
 *
 * Search controls for cashflow data.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { Input } from '@/components/ui/input';
import { Search, X } from 'lucide-react';
import { useState } from 'react';

/**
 * Cashflow Search Props
 */
interface CashflowSearchProps {
  onSearch: (query: string) => void;
  onClear: () => void;
}

/**
 * Cashflow Search Component
 *
 * Provides search input for filtering transactions.
 */
export function CashflowSearch({ onSearch, onClear }: CashflowSearchProps) {
  const [query, setQuery] = useState('');

  const handleSearch = (value: string) => {
    setQuery(value);
    onSearch(value);
  };

  const handleClear = () => {
    setQuery('');
    onClear();
  };

  return (
    <div className="relative w-full max-w-sm">
      <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
      <Input
        placeholder="Search transactions..."
        className="pl-8 pr-8"
        value={query}
        onChange={(e) => handleSearch(e.target.value)}
      />
      {query && (
        <button
          onClick={handleClear}
          className="absolute right-2 top-2.5 h-4 w-4 text-gray-500 hover:text-gray-700"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}