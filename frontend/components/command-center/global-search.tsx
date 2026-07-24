/**
 * Global Search - Stage 5 Command Center Platform
 *
 * Cross-workspace search returning graph nodes.
 * Searches: transactions, merchants, categories, accounts, cards, loans, investments, forecasts, behaviors.
 */

'use client';

import { useState, useMemo, useCallback } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import type { GraphNode } from '@/lib/graph';
import { formatINR } from '@/lib/utils/format';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';

// ===== Props =====
interface GlobalSearchProps {
  onNodeSelect?: (node: GraphNode) => void;
  className?: string;
}

// ===== Component =====
export function GlobalSearch({
  onNodeSelect,
  className = '',
}: GlobalSearchProps) {
  const [query, setQuery] = useState('');
  const [showResults, setShowResults] = useState(false);

  // Get current graph
  const graph = commandCenterRuntime.getCurrentGraph();

  // Search nodes
  const searchResults = useMemo(() => {
    if (!query || !graph) return [];

    const lowerQuery = query.toLowerCase();
    return graph.nodes.filter(node =>
      node.label.toLowerCase().includes(lowerQuery) ||
      node.workspace.toLowerCase().includes(lowerQuery) ||
      (node.metadata && Object.values(node.metadata).some(v =>
        String(v).toLowerCase().includes(lowerQuery),
      )),
    ).slice(0, 20);
  }, [query, graph]);

  // Handle node selection
  const handleSelect = useCallback(
    (node: GraphNode) => {
      setQuery('');
      setShowResults(false);
      onNodeSelect?.(node);
    },
    [onNodeSelect],
  );

  return (
    <div className={`relative ${className}`}>
      <Input
        type="text"
        placeholder="Search transactions, accounts, loans, investments..."
        value={query}
        onChange={e => {
          setQuery(e.target.value);
          setShowResults(true);
        }}
        onFocus={() => setShowResults(true)}
        onBlur={() => setTimeout(() => setShowResults(false), 200)}
        className="w-full"
      />

      {/* Search Results */}
      {showResults && searchResults.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 max-h-64 overflow-y-auto bg-white border rounded-md shadow-lg z-10">
          {searchResults.map(node => (
            <Card
              key={node.id}
              className="m-1 cursor-pointer hover:bg-gray-50"
              onClick={() => handleSelect(node)}
            >
              <CardContent className="p-2">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{node.label}</p>
                    <p className="text-xs text-gray-500">{node.workspace}</p>
                  </div>
                  {node.value_paise !== undefined && (
                    <span className="text-xs text-gray-700">
                      {formatINR(node.value_paise)}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* No Results */}
      {showResults && query && searchResults.length === 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 p-2 bg-white border rounded-md shadow-lg z-10">
          <p className="text-sm text-gray-500">No results found</p>
        </div>
      )}
    </div>
  );
}