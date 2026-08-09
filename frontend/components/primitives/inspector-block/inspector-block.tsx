/**
 * Inspector Block - Stage 8H Premium Financial OS Polish
 *
 * Reusable inspector section component.
 * Density-optimized progressive disclosure block.
 * Answers: What is selected? Why does it matter? What next?
 */

'use client';

import type { ReactNode} from 'react';
import { useState } from 'react';
import { Surface } from '@/components/primitives/surface/surface';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight } from 'lucide-react';

// ===== Props =====
interface InspectorBlockProps {
  title: string;
  children: ReactNode;
  className?: string;
  defaultOpen?: boolean;
  collapsible?: boolean;
  badge?: ReactNode;
}

// ===== Inspector Block Component =====
export function InspectorBlock({
  title,
  children,
  className,
  defaultOpen = true,
  collapsible = false,
  badge,
}: InspectorBlockProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Surface
      variant="raised"
      density="compact"
      className={cn(
        'border-0 border-b border-[var(--border-subtle)] last:border-b-0 rounded-none',
        className,
      )}
    >
      <button
        type="button"
        className={cn(
          'flex w-full items-center gap-1.5 px-3 py-1.5 border-b border-[var(--border-subtle)]',
          'text-left hover:bg-[var(--surface-interactive)] transition-colors duration-100',
          !collapsible && 'cursor-default hover:bg-transparent',
        )}
        onClick={collapsible ? () => setOpen((v) => !v) : undefined}
        aria-expanded={collapsible ? open : undefined}
        disabled={!collapsible}
      >
        {collapsible && (
          open
            ? <ChevronDown className="h-3 w-3 text-[var(--text-tertiary)] shrink-0" />
            : <ChevronRight className="h-3 w-3 text-[var(--text-tertiary)] shrink-0" />
        )}
        <span className="fin-caption font-medium uppercase tracking-wider text-[var(--text-tertiary)] flex-1">
          {title}
        </span>
        {badge}
      </button>
      {open && (
        <div className="px-3 py-2">
          {children}
        </div>
      )}
    </Surface>
  );
}
