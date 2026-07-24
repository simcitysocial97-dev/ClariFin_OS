/**
 * Search Result - Stage 8F Financial OS Interaction Layer
 *
 * Individual search result item.
 */

'use client';

import { cn } from '@/lib/utils';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import type { SearchResult, SearchResultType } from '@/lib/interaction/interaction-types';

// ===== Icon Map =====
const typeIcons: Record<SearchResultType, string> = {
  transaction: 'receipt',
  account: 'wallet',
  loan: 'landmark',
  investment: 'trending-up',
  goal: 'target',
  rule: 'filter',
  forecast: 'crystal-ball',
  merchant: 'store',
  category: 'tag',
  tag: 'tag',
  insight: 'lightbulb',
  command: 'command',
  workspace: 'layout-dashboard',
};

// ===== Props =====
interface SearchResultProps {
  result: SearchResult;
  selected?: boolean;
  onSelect?: () => void;
}

// ===== Component =====
export function SearchResult({ result, selected = false, onSelect }: SearchResultProps) {
  const icon = typeIcons[result.type] || 'search';

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-3 py-2 cursor-pointer transition-colors',
        selected
          ? 'bg-[var(--surface-selected)] text-[var(--text-primary)]'
          : 'text-[var(--text-secondary)] hover:bg-[var(--surface-interactive)]',
      )}
      onClick={onSelect}
      role="option"
      aria-selected={selected}
    >
      <FinancialIcon
        name={icon}
        size={16}
        className={selected ? 'text-[var(--color-selection)]' : 'text-[var(--text-tertiary)]'}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className={cn('text-sm font-medium truncate', selected && 'text-[var(--text-primary)]')}>
            {result.label}
          </span>
          {result.value_paise !== undefined && (
            <span className="text-xs text-[var(--text-tertiary)]">
              {formatINR(result.value_paise)}
            </span>
          )}
        </div>
        {result.description && (
          <p className="text-xs text-[var(--text-tertiary)] truncate mt-0.5">{result.description}</p>
        )}
        {result.workspace && (
          <p className="text-xs text-[var(--text-tertiary)] truncate mt-0.5">
            in {result.workspace}
          </p>
        )}
      </div>
    </div>
  );
}

// ===== Helper =====
function formatINR(paise: number): string {
  const rupees = paise / 100;
  return `₹${rupees.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}