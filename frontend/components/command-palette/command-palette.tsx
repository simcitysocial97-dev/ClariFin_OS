/**
 * Command Palette - Stage 5 Command Center Experience
 *
 * Universal command interface for the Financial OS.
 * Supports: command search, recent commands, workspace navigation, keyboard shortcuts.
 * Opens with Cmd/Ctrl+K.
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { useCommandContext } from './command-provider';
import { CommandItem } from './command-item';
import { Kbd } from '@/components/primitives/kbd';
import { formatRelativeTime } from '@/lib/utils/format';

// ===== Props =====
interface CommandPaletteProps {
  className?: string;
}

// ===== Component =====
export function CommandPalette({ className }: CommandPaletteProps) {
  const {
    open,
    query,
    selectedIndex,
    filteredCommands,
    recentCommands,
    closePalette,
    setQuery,
    selectNext,
    selectPrevious,
    executeSelected,
  } = useCommandContext();

  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input when opened
  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  // Handle keyboard events
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          selectNext();
          break;
        case 'ArrowUp':
          event.preventDefault();
          selectPrevious();
          break;
        case 'Enter':
          event.preventDefault();
          executeSelected();
          break;
        case 'Escape':
          event.preventDefault();
          closePalette();
          break;
      }
    },
    [selectNext, selectPrevious, executeSelected, closePalette],
  );

  if (!open) return null;

  const displayCommands = filteredCommands.length > 0 ? filteredCommands : [];
  const showRecent = !query && recentCommands.length > 0;

  return (
    <div
      className={cn(
        'fixed inset-0 z-[1000] flex items-start justify-center pt-32',
        'bg-black/50 backdrop-blur-sm',
        className,
      )}
      onClick={closePalette}
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div
        className="w-full max-w-md bg-[var(--surface-default)] border border-[var(--border-default)] rounded-[var(--radius-lg)] shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Input */}
        <div className="p-3 border-b border-[var(--border-default)]">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search commands or type a workspace name..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--text-tertiary)]"
            aria-label="Command search"
            autoComplete="off"
          />
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto" role="listbox">
          {displayCommands.length > 0 ? (
            displayCommands.map((result, index) => (
              <CommandItem
                id={result.command.id}
                key={result.command.id}
                label={result.command.label}
                description={result.command.keywords?.join(', ')}
                icon={result.command.icon}
                shortcut={result.command.shortcut}
                selected={index === selectedIndex}
                onSelect={async () => {
                  await executeSelected();
                }}
              />
            ))
          ) : showRecent ? (
            /* Recent commands section */
            <div className="p-2">
              <div className="px-3 py-1.5 text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">
                Recent
              </div>
              {recentCommands.map((entry, index) => (
                <button
                  key={`${entry.commandId}-${entry.timestamp}`}
                  className={cn(
                    'w-full flex items-center justify-between px-3 py-2 text-left transition-colors',
                    index === 0
                      ? 'bg-[var(--surface-selected)] text-[var(--text-primary)]'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--surface-interactive)]',
                  )}
                  onClick={async () => {
                    await executeSelected();
                  }}
                  role="option"
                  aria-selected={index === 0}
                >
                  <span className="text-sm truncate">{entry.input}</span>
                  <span className="text-xs text-[var(--text-tertiary)] ml-2 shrink-0">
                    {formatRelativeTime(entry.timestamp)}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-3 text-sm text-[var(--text-tertiary)]">
              {query ? 'No commands found' : 'Type to search commands'}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-2 border-t border-[var(--border-default)] text-xs text-[var(--text-tertiary)] flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Kbd keys={['↑']} />
            <Kbd keys={['↓']} />
            <span className="ml-1">navigate</span>
          </div>
          <div className="flex items-center gap-1">
            <Kbd keys={['↵']} />
            <span>execute</span>
          </div>
          <div className="flex items-center gap-1">
            <Kbd keys={['esc']} />
            <span>close</span>
          </div>
        </div>
      </div>
    </div>
  );
}