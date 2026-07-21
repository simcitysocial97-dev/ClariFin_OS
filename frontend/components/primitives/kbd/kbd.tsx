/**
 * Kbd - Stage 8E Keyboard Shortcut Display
 *
 * Displays keyboard shortcuts with consistent monospace styling.
 * Inspired by Cursor IDE / Linear keyboard shortcut display.
 */

import { cn } from '@/lib/utils';

interface KbdProps extends React.HTMLAttributes<HTMLElement> {
  keys: string[];
  size?: 'sm' | 'md';
}

export function Kbd({
  keys,
  size = 'sm',
  className,
  ...props
}: KbdProps) {
  const keyLabels: Record<string, string> = {
    mod: '⌘',
    cmd: '⌘',
    ctrl: '⌃',
    alt: '⌥',
    shift: '⇧',
    enter: '↵',
    escape: 'esc',
    tab: '⇥',
    delete: '⌫',
    up: '↑',
    down: '↓',
    left: '←',
    right: '→',
    space: '␣',
  };

  return (
    <kbd
      className={cn(
        'inline-flex items-center gap-0.5 font-mono leading-none',
        size === 'sm' ? 'text-[10px]' : 'text-xs',
        className
      )}
      {...props}
    >
      {keys.map((key, i) => (
        <span
          key={i}
          className={cn(
            'inline-flex items-center justify-center rounded-[2px] bg-[var(--surface-selected)] text-[var(--text-secondary)]',
            size === 'sm' ? 'h-3.5 min-w-[14px] px-[2px]' : 'h-4 min-w-[16px] px-1',
          )}
        >
          {keyLabels[key.toLowerCase()] || key.toUpperCase()}
        </span>
      ))}
    </kbd>
  );
}

// ===== Shortcut Hint =====
interface ShortcutHintProps extends React.HTMLAttributes<HTMLSpanElement> {
  shortcut: string;
  description?: string;
}

export function ShortcutHint({
  shortcut,
  description,
  className,
  ...props
}: ShortcutHintProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 text-[10px] text-[var(--text-tertiary)]',
        className
      )}
      {...props}
    >
      {description && <span>{description}</span>}
      <Kbd keys={shortcut.split('+')} size="sm" />
    </span>
  );
}