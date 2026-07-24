/**
 * Transaction Search Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for transaction search.
 */

'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Search, X } from 'lucide-react';

interface TransactionSearchProps {
  value: string;
  onChange: (query: string) => void;
  placeholder?: string;
}

/**
 * Transaction Search Component
 * Provides text input for searching transactions
 */
export function TransactionSearch({
  value,
  onChange,
  placeholder = 'Search transactions...',
}: TransactionSearchProps) {
  const [query, setQuery] = useState(value);

  // Debounce the search
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query, onChange]);

  const handleClear = () => {
    setQuery('');
    onChange('');
  };

  return (
    <div className="relative w-full max-w-sm">
      <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        type="search"
        placeholder={placeholder}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="pl-8 pr-8"
      />
      {query && (
        <button
          onClick={handleClear}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}