/**
 * Stack - Stage 8E Layout Primitive
 *
 * Vertical or horizontal stacking with consistent spacing.
 */

import { cn } from '@/lib/utils';

interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: 'vertical' | 'horizontal';
  gap?: 0 | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 4 | 5 | 6 | 8 | 10 | 12;
  wrap?: boolean;
  align?: 'start' | 'center' | 'end' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
}

const gapClasses: Record<NonNullable<StackProps['gap']>, string> = {
  0: 'gap-0', 0.5: 'gap-0.5', 1: 'gap-1', 1.5: 'gap-1.5',
  2: 'gap-2', 2.5: 'gap-2.5', 3: 'gap-3', 4: 'gap-4',
  5: 'gap-5', 6: 'gap-6', 8: 'gap-8', 10: 'gap-10', 12: 'gap-12',
};

const alignClasses: Record<NonNullable<StackProps['align']>, string> = {
  start: 'items-start', center: 'items-center', end: 'items-end', stretch: 'items-stretch',
};

const justifyClasses: Record<NonNullable<StackProps['justify']>, string> = {
  start: 'justify-start', center: 'justify-center', end: 'justify-end',
  between: 'justify-between', around: 'justify-around', evenly: 'justify-evenly',
};

export function Stack({
  className,
  direction = 'vertical',
  gap = 2,
  wrap = false,
  align = 'stretch',
  justify = 'start',
  children,
  ...props
}: StackProps) {
  return (
    <div
      className={cn(
        direction === 'vertical' ? 'flex flex-col' : 'flex flex-row',
        gapClasses[gap],
        wrap && 'flex-wrap',
        alignClasses[align],
        justifyClasses[justify],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}