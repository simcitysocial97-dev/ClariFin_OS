/**
 * Cluster - Stage 8E Layout Primitive
 *
 * Auto-wrapping horizontal layout with consistent spacing.
 * Perfect for tags, badges, chips.
 */

import { cn } from '@/lib/utils';

interface ClusterProps extends React.HTMLAttributes<HTMLDivElement> {
  gap?: 0 | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 4 | 5 | 6 | 8;
  align?: 'start' | 'center' | 'end';
  justify?: 'start' | 'center' | 'end';
}

const gapClasses: Record<NonNullable<ClusterProps['gap']>, string> = {
  0: 'gap-0', 0.5: 'gap-0.5', 1: 'gap-1', 1.5: 'gap-1.5',
  2: 'gap-2', 2.5: 'gap-2.5', 3: 'gap-3', 4: 'gap-4',
  5: 'gap-5', 6: 'gap-6', 8: 'gap-8',
};

export function Cluster({
  className,
  gap = 1,
  align = 'center',
  justify = 'start',
  children,
  ...props
}: ClusterProps) {
  return (
    <div
      className={cn(
        'flex flex-wrap',
        gapClasses[gap],
        `items-${align}`,
        `justify-${justify}`,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}