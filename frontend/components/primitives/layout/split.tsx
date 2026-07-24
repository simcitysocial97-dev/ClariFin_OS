/**
 * Split - Stage 8E Layout Primitive
 *
 * Two-panel split layout with optional resizable divider.
 */

import { cn } from '@/lib/utils';

interface SplitProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: 'horizontal' | 'vertical';
  ratio?: string; // e.g. '1fr 1fr', '2fr 1fr', '300px 1fr'
  gap?: 0 | 1 | 2 | 3 | 4 | 6 | 8;
}

const gapClasses: Record<NonNullable<SplitProps['gap']>, string> = {
  0: 'gap-0', 1: 'gap-1', 2: 'gap-2', 3: 'gap-3', 4: 'gap-4', 6: 'gap-6', 8: 'gap-8',
};

export function Split({
  className,
  direction = 'horizontal',
  ratio = '1fr 1fr',
  gap = 0,
  children,
  style,
  ...props
}: SplitProps) {
  return (
    <div
      className={cn(
        direction === 'horizontal' ? 'flex flex-row' : 'flex flex-col',
        gapClasses[gap],
        className
      )}
      style={{
        ...style,
        ...(direction === 'horizontal'
          ? { gridTemplateColumns: ratio }
          : { gridTemplateRows: ratio }),
      }}
      {...props}
    >
      {children}
    </div>
  );
}