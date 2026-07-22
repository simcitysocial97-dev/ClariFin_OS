/**
 * Command Palette - Stage 8F Financial OS Interaction Layer
 *
 * Universal command interface for the Financial OS.
 * Discovers commands from WorkspaceRegistry.
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { useCommandContext } from './command-provider';
import { CommandItem } from './command-item';
import { Kbd } from '@/components/primitives/kbd';

// ===== Props =====
interface CommandPaletteProps {
  className?: string;
}

// ===== Component =====
export function CommandPalette({ className }: CommandPaletteProps) {
  const { state, closePalette, setQuery, selectNext, selectPrevious, executeSelected } =
    useCommandContext();
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input when opened
  useEffect(() => {
    if (state.open) {
      inputRef.current?.focus();
    }
  }, [state.open]);

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

  if (!state.open) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-start justify-center pt-32',
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
            placeholder="Type a command..."
            value={state.query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--text-tertiary)]"
            aria-label="Command search"
            autoComplete="off"
          />
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto" role="listbox">
          {state.filteredCommands.length === 0 ? (
            <div className="p-3 text-sm text-[var(--text-tertiary)]">No commands found</div>
          ) : (
            state.filteredCommands.map((command, index) => (
              <CommandItem
                id={command.id}
                key={command.id}
                label={command.label}
                description={command.description}
                icon={command.icon}
                shortcut={command.shortcut}
                selected={index === state.selectedIndex}
                onSelect={async () => {
                  // Set this command as selected and execute
                  setQuery(command.label);
                  await executeSelected();
                }}
              />
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-2 border-t border-[var(--border-default)] text-xs text-[var(--text-tertiary)] flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Kbd keys={['↑']} />
            <Kbd keys={['↓']} />
            <span className="ml-1">to navigate</span>
          </div>
          <div className="flex items-center gap-1">
            <Kbd keys={['↵']} />
            <span>to execute</span>
          </div>
        </div>
      </div>
    </div>
  );
}