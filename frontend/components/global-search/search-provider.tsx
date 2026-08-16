/**
 * Search Provider - Stage 8F Financial OS Interaction Layer
 *
 * Provides global search context to the application.
 * Searches across all entity types.
 */

'use client';

import { createContext, useContext, useMemo, useCallback, useState } from 'react';
import type { SearchResult, SearchResultType } from '@/lib/interaction/interaction-types';
import type { WorkspaceName } from '@/lib/workspace';
import { commandCenterRuntime } from '@/lib/command-center';

// ===== Context Types =====
interface SearchContextValue {
  query: string;
  results: SearchResult[];
  setQuery: (query: string) => void;
  openSearch: () => void;
  closeSearch: () => void;
  isOpen: boolean;
}

// ===== Context =====
const SearchContext = createContext<SearchContextValue | null>(null);

// ===== Provider =====
interface SearchProviderProps {
  children: React.ReactNode;
}

export function SearchProvider({ children }: SearchProviderProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  // Get graph data for searching
  const graph = commandCenterRuntime.getCurrentGraph();

  // Search across all entity types
  const results = useMemo(() => {
    if (!query || !graph) return [];

    const lowerQuery = query.toLowerCase();
    const searchResults: SearchResult[] = [];

    // Search nodes
    for (const node of graph.nodes) {
      if (
        node.label.toLowerCase().includes(lowerQuery) ||
        node.workspace.toLowerCase().includes(lowerQuery) ||
        (node.metadata && Object.values(node.metadata).some(v => String(v).toLowerCase().includes(lowerQuery)))
      ) {
        searchResults.push({
          id: node.id,
          type: node.type as SearchResultType,
          label: node.label,
          workspace: node.workspace as WorkspaceName,
          value_paise: node.value_paise,
          metadata: node.metadata,
        });
      }
    }

    return searchResults;
  }, [query, graph]);

  const openSearch = useCallback(() => {
    setIsOpen(true);
  }, []);

  const closeSearch = useCallback(() => {
    setIsOpen(false);
    setQuery('');
  }, []);

  const value = useMemo<SearchContextValue>(
    () => ({
      query,
      results,
      setQuery,
      openSearch,
      closeSearch,
      isOpen,
    }),
    [query, results, openSearch, closeSearch, isOpen],
  );

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
}

// ===== Hook =====
export function useSearchContext(): SearchContextValue {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error('useSearchContext must be used within SearchProvider');
  }
  return context;
}