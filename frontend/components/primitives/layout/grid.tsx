/**
 * Grid - Stage 8E Layout Primitive
 *
 * CSS grid layout with configurable columns and consistent spacing.
 */

import { cn } from '@/lib/utils';

interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  columns?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  gap?: 0 | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 4 | 5 | 6 | 8 | 10 | 12;
}

const columnClasses: Record<NonNullable<GridProps['columns']>, string> = {
  1: 'grid-cols-1', 2: 'grid-cols-2', 3: 'grid-cols-3', 4: 'grid-cols-4',
  5: 'grid-cols-5', 6: 'grid-cols-6', 7: 'grid-cols-7', 8: 'grid-cols-8',
  9: 'grid-cols-9', 10: 'grid-cols-10', 11: 'grid-cols-11', 12: 'grid-cols-12',
};

const gapClasses: Record<NonNullable<GridProps['gap']>, string> = {
  0: 'gap-0', 0.5: 'gap-0.5', 1: 'gap-1', 1.5: 'gap-1.5',
  2: 'gap-2', 2.5: 'gap-2.5', 3: 'gap-3', 4: 'gap-4',
  5: 'gap-5', 6: 'gap-6', 8: 'gap-8', 10: 'gap-10', 12: 'gap-12',
};

export function Grid({
  className,
  columns = 1,
  gap = 4,
  children,
  ...props
}: GridProps) {
  return (
    <div
      className={cn(
        'grid',
        columnClasses[columns],
        gapClasses[gap],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}