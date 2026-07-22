/**
 * Command Item - Stage 8F Financial OS Interaction Layer
 *
 * Individual command item in the command palette.
 */

'use client';

import { cn } from '@/lib/utils';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';

// ===== Props =====
interface CommandItemProps {
  id: string;
  label: string;
  description?: string;
  icon?: string;
  shortcut?: string;
  selected?: boolean;
  onSelect?: () => void;
}

// ===== Component =====
export function CommandItem({
  id,
  label,
  description,
  icon,
  shortcut,
  selected = false,
  onSelect,
}: CommandItemProps) {
  return (
    <div
      data-command-id={id}
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
      {icon && (
        <FinancialIcon
          name={icon}
          size={16}
          className={selected ? 'text-[var(--color-selection)]' : 'text-[var(--text-tertiary)]'}
        />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className={cn('text-sm font-medium truncate', selected && 'text-[var(--text-primary)]')}>
            {label}
          </span>
          {shortcut && (
            <kbd className="px-1.5 py-0.5 text-xs bg-[var(--surface-raised)] border border-[var(--border-default)] rounded-[var(--radius-sm)]">
              {shortcut}
            </kbd>
          )}
        </div>
        {description && (
          <p className="text-xs text-[var(--text-tertiary)] truncate mt-0.5">{description}</p>
        )}
      </div>
    </div>
  );
}