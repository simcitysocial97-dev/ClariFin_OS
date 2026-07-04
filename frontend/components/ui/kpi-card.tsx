'use client';

import { cva, type VariantProps } from 'class-variance-authority';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { ArrowDown, ArrowUp, Minus } from 'lucide-react';

const kpiCardVariants = cva(
  'rounded-xl border bg-card p-5 transition-colors',
  {
    variants: {
      variant: {
        default: '',
        danger: 'border-red-200 bg-red-50/50 dark:border-red-900 dark:bg-red-950/20',
        success: 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/20',
        warning: 'border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

interface KpiCardProps {
  title: string;
  value: string;
  subtext?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: React.ReactNode;
  variant?: VariantProps<typeof kpiCardVariants>['variant'];
  loading?: boolean;
}

export function KpiCard({
  title,
  value,
  subtext,
  trend,
  trendValue,
  icon,
  variant = 'default',
  loading = false,
}: KpiCardProps) {
  if (loading) {
    return (
      <div className={cn(kpiCardVariants({ variant }))}>
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="h-5 w-5 rounded-full" />
        </div>
      </div>
    );
  }

  const trendColors = {
    up: 'text-emerald-600 dark:text-emerald-400',
    down: 'text-red-600 dark:text-red-400',
    neutral: 'text-muted-foreground',
  };

  const TrendIcon = trend === 'up' ? ArrowUp : trend === 'down' ? ArrowDown : Minus;

  return (
    <div className={cn(kpiCardVariants({ variant }))}>
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {(trendValue || subtext) && (
            <div className="flex items-center gap-2">
              {trendValue && trend && (
                <span className={cn('inline-flex items-center gap-0.5 text-xs font-medium', trendColors[trend])}>
                  <TrendIcon className="h-3 w-3" />
                  {trendValue}
                </span>
              )}
              {subtext && <span className="text-xs text-muted-foreground">{subtext}</span>}
            </div>
          )}
        </div>
        {icon && (
          <div className="text-muted-foreground/60">{icon}</div>
        )}
      </div>
    </div>
  );
}