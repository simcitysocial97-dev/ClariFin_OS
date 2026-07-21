/**
 * ScrollRegion - Stage 8E Layout Primitive
 *
 * Scrollable container with consistent styling.
 * Thin scrollbars aligned to Financial OS theme.
 */

import { cn } from '@/lib/utils';

interface ScrollRegionProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'vertical' | 'horizontal' | 'both';
  hideScrollbar?: boolean;
}

const overflowClasses: Record<NonNullable<ScrollRegionProps['orientation']>, string> = {
  vertical: 'overflow-y-auto',
  horizontal: 'overflow-x-auto',
  both: 'overflow-auto',
};

export function ScrollRegion({
  className,
  orientation = 'vertical',
  hideScrollbar = false,
  children,
  ...props
}: ScrollRegionProps) {
  return (
    <div
      className={cn(
        overflowClasses[orientation],
        hideScrollbar && 'scrollbar-none',
        '[&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar]:h-1.5',
        '[&::-webkit-scrollbar-track]:bg-transparent',
        '[&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-[var(--border-strong)]',
        '[&::-webkit-scrollbar-thumb:hover]:bg-[var(--text-tertiary)]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}