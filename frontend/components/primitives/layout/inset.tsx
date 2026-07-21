/**
 * Inset - Stage 8E Layout Primitive
 *
 * Consistent padding wrapper.
 * Padding values follow the 8px spacing system.
 */

import { cn } from '@/lib/utils';

interface InsetProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 0 | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 4 | 5 | 6 | 8 | 10 | 12;
  horizontal?: 0 | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 4 | 5 | 6 | 8 | 10 | 12;
  vertical?: 0 | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 4 | 5 | 6 | 8 | 10 | 12;
}

const padClasses: Record<number, string> = {
  0: 'p-0', 0.5: 'p-0.5', 1: 'p-1', 1.5: 'p-1.5',
  2: 'p-2', 2.5: 'p-2.5', 3: 'p-3', 4: 'p-4',
  5: 'p-5', 6: 'p-6', 8: 'p-8', 10: 'p-10', 12: 'p-12',
};

const pxClasses: Record<number, string> = {
  0: 'px-0', 0.5: 'px-0.5', 1: 'px-1', 1.5: 'px-1.5',
  2: 'px-2', 2.5: 'px-2.5', 3: 'px-3', 4: 'px-4',
  5: 'px-5', 6: 'px-6', 8: 'px-8', 10: 'px-10', 12: 'px-12',
};

const pyClasses: Record<number, string> = {
  0: 'py-0', 0.5: 'py-0.5', 1: 'py-1', 1.5: 'py-1.5',
  2: 'py-2', 2.5: 'py-2.5', 3: 'py-3', 4: 'py-4',
  5: 'py-5', 6: 'py-6', 8: 'py-8', 10: 'py-10', 12: 'py-12',
};

export function Inset({
  className,
  padding,
  horizontal,
  vertical,
  children,
  ...props
}: InsetProps) {
  const classes = padding !== undefined
    ? padClasses[padding]
    : cn(
        horizontal !== undefined && pxClasses[horizontal],
        vertical !== undefined && pyClasses[vertical]
      );

  return (
    <div className={cn(classes, className)} {...props}>
      {children}
    </div>
  );
}