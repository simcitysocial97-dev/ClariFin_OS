/**
 * Global Search - Stage 8F Financial OS Interaction Layer
 *
 * Full-screen global search interface.
 * Searches across all entity types.
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { useSearchContext } from './search-provider';
import { SearchResult } from './search-result';
import { Kbd } from '@/components/primitives/kbd';

// ===== Props =====
interface GlobalSearchProps {
  className?: string;
  onNodeSelect?: (nodeId: string) => void;
}

// ===== Component =====
export function GlobalSearch({ className, onNodeSelect }: GlobalSearchProps) {
  const { query, results, setQuery, closeSearch, isOpen } = useSearchContext();
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input when opened
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Handle keyboard events
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      switch (event.key) {
        case 'Escape':
          event.preventDefault();
          closeSearch();
          break;
        case 'Enter':
          if (results.length > 0) {
            onNodeSelect?.(results[0].id);
            closeSearch();
          }
          break;
      }
    },
    [closeSearch, results, onNodeSelect],
  );

  if (!isOpen) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-start justify-center pt-32',
        'bg-black/50 backdrop-blur-sm',
        className,
      )}
      onClick={closeSearch}
      role="dialog"
      aria-modal="true"
      aria-label="Global search"
    >
      <div
        className="w-full max-w-2xl bg-[var(--surface-default)] border border-[var(--border-default)] rounded-[var(--radius-lg)] shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Input */}
        <div className="p-3 border-b border-[var(--border-default)]">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search transactions, accounts, loans, investments, goals, rules..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--text-tertiary)]"
            aria-label="Global search"
            autoComplete="off"
          />
        </div>

        {/* Results grouped by type */}
        <div className="max-h-96 overflow-y-auto" role="listbox">
          {results.length === 0 && query ? (
            <div className="p-3 text-sm text-[var(--text-tertiary)]">No results found</div>
          ) : (
            <div className="divide-y divide-[var(--border-subtle)]">
              {results.map((result, index) => (
                <SearchResult
                  key={result.id}
                  result={result}
                  selected={index === 0}
                  onSelect={() => {
                    onNodeSelect?.(result.id);
                    closeSearch();
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-2 border-t border-[var(--border-default)] text-xs text-[var(--text-tertiary)] flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Kbd keys={['↵']} />
            <span className="ml-1">to select</span>
          </div>
          <div className="flex items-center gap-1">
            <Kbd keys={['esc']} />
            <span>to close</span>
          </div>
        </div>
      </div>
    </div>
  );
}