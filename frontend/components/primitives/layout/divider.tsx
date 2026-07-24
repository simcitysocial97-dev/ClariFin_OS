/**
 * Divider - Stage 8E Layout Primitive
 *
 * Visual separator between sections.
 * Uses existing shadcn Separator under the hood.
 */

import { cn } from '@/lib/utils';

interface DividerProps extends React.HTMLAttributes<HTMLHRElement> {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'subtle' | 'default' | 'strong';
}

export function Divider({
  className,
  orientation = 'horizontal',
  ...props
}: DividerProps) {
  return (
    <hr
      className={cn(
        'border-0 bg-[var(--border-default)]',
        orientation === 'horizontal' ? 'h-px w-full' : 'h-full w-px',
        className
      )}
      {...props}
    />
  );
}