/**
 * Reconciliation Search - Stage 4 Reconciliation Intelligence Workspace
 *
 * Search reconciliation by transaction or statement.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Search, X } from 'lucide-react';

/**
 * Reconciliation Search Props
 */
interface ReconciliationSearchProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

/**
 * Reconciliation Search Component
 */
export function ReconciliationSearch({ searchQuery, onSearchChange }: ReconciliationSearchProps) {
  const [localQuery, setLocalQuery] = useState(searchQuery);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(localQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [localQuery, onSearchChange]);

  // Handle keyboard shortcut (Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const input = document.getElementById('reconciliation-search');
        input?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
      <Input
        id="reconciliation-search"
        type="text"
        placeholder="Search reconciliation..."
        value={localQuery}
        onChange={(e) => setLocalQuery(e.target.value)}
        className="pl-10 pr-10 w-full sm:w-64"
        aria-label="Search reconciliation"
      />
      {localQuery && (
        <button
          onClick={() => setLocalQuery('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}