/**
 * Shortcut Overlay - Stage 8F Financial OS Interaction Layer
 *
 * Displays all available keyboard shortcuts.
 * Shows OS-level and workspace-specific shortcuts.
 */

'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { keyboardRegistry } from '@/lib/interaction/keyboard-registry';
import type { KeyboardShortcut } from '@/lib/interaction/interaction-types';

// ===== Props =====
interface ShortcutOverlayProps {
  className?: string;
}

// ===== Component =====
export function ShortcutOverlay({ className }: ShortcutOverlayProps) {
  const [open, setOpen] = useState(false);
  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>([]);

  // Listen for show-shortcuts event
  useEffect(() => {
    const handleShowShortcuts = () => {
      setOpen(true);
      setShortcuts(keyboardRegistry.getAll());
    };

    window.addEventListener('os-show-shortcuts', handleShowShortcuts);
    return () => {
      window.removeEventListener('os-show-shortcuts', handleShowShortcuts);
    };
  }, []);

  // Group shortcuts by category
  const groupedShortcuts = shortcuts.reduce(
    (acc, shortcut) => {
      const category = shortcut.category;
      if (!acc[category]) acc[category] = [];
      acc[category].push(shortcut);
      return acc;
    },
    {} as Record<string, KeyboardShortcut[]>,
  );

  if (!open) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center',
        'bg-black/50 backdrop-blur-sm',
        className,
      )}
      onClick={() => setOpen(false)}
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
    >
      <div
        className="w-full max-w-2xl bg-[var(--surface-default)] border border-[var(--border-default)] rounded-[var(--radius-lg)] shadow-xl p-4"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold mb-4">Keyboard Shortcuts</h2>

        <div className="space-y-4 max-h-96 overflow-y-auto">
          {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => (
            <div key={category}>
              <h3 className="text-sm font-medium text-[var(--text-tertiary)] mb-2 capitalize">
                {category}
              </h3>
              <div className="space-y-1">
                {categoryShortcuts.map(shortcut => (
                  <div
                    key={shortcut.key}
                    className="flex items-center justify-between py-1 px-2 text-sm"
                  >
                    <span className="text-[var(--text-secondary)]">{shortcut.description}</span>
                    <kbd className="px-2 py-1 text-xs bg-[var(--surface-raised)] border border-[var(--border-default)] rounded-[var(--radius-sm)]">
                      {formatShortcut(shortcut)}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-3 border-t border-[var(--border-default)] text-xs text-[var(--text-tertiary)]">
          Press <kbd className="px-1 py-0.5 bg-[var(--surface-raised)] border border-[var(--border-default)] rounded">?</kbd> to show shortcuts
        </div>
      </div>
    </div>
  );
}

// ===== Helper =====
function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];
  if (shortcut.ctrl) parts.push('Ctrl');
  if (shortcut.cmd) parts.push('Cmd');
  if (shortcut.alt) parts.push('Alt');
  if (shortcut.shift) parts.push('Shift');
  parts.push(shortcut.key.toUpperCase());
  return parts.join('+');
}