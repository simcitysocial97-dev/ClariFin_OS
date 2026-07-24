/**
 * CompactToolbar - Stage 8E Toolbar Primitive
 *
 * Icon-first compact toolbar for workspace controls.
 * Minimal, dense, tooltip-driven.
 */

'use client';

import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Divider } from '@/components/primitives/layout/divider';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';

export const toolbarVariants = cva(
  'flex items-center gap-0.5',
  {
    variants: {
      size: {
        sm: 'h-7',
        md: 'h-8',
        default: 'h-9',
      },
      divided: {
        true: 'gap-0',
        false: '',
      },
    },
    defaultVariants: {
      size: 'md',
      divided: false,
    },
  }
);

interface CompactToolbarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof toolbarVariants> {
  divided?: boolean;
}

export function CompactToolbar({
  className,
  size = 'md',
  divided = false,
  children,
  ...props
}: CompactToolbarProps) {
  return (
    <div
      className={cn(toolbarVariants({ size, divided }), className)}
      {...props}
    >
      {children}
    </div>
  );
}

// ===== Toolbar Button =====
interface ToolbarButtonProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
  shortcut?: string;
}

export function ToolbarButton({
  icon: Icon,
  label,
  onClick,
  active = false,
  disabled = false,
  shortcut,
}: ToolbarButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span>
          <Button
            variant={active ? 'secondary' : 'ghost'}
            size="icon-sm"
            disabled={disabled}
            onClick={onClick}
            data-active={active}
            className={cn(
              'relative',
              active && 'bg-[var(--surface-selected)] text-[var(--text-primary)]'
            )}
          >
            <Icon className="h-4 w-4" />
          </Button>
        </span>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        {label}{shortcut ? ` (${shortcut})` : ''}
      </TooltipContent>
    </Tooltip>
  );
}

// ===== Toolbar Separator =====
export function ToolbarSeparator() {
  return <Divider orientation="vertical" className="mx-1 h-4" />;
}

// ===== Toolbar Label =====
interface ToolbarLabelProps extends React.HTMLAttributes<HTMLSpanElement> {
  label: string;
}

export function ToolbarLabel({
  label,
  className,
  ...props
}: ToolbarLabelProps) {
  return (
    <span
      className={cn(
        'text-xs font-medium text-[var(--text-tertiary)] px-1.5 select-none',
        className
      )}
      {...props}
    >
      {label}
    </span>
  );
}