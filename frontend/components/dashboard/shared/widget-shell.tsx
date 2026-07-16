/**
 * WidgetShell - Consistent container for all widgets with loading/error/empty states
 */

import type { BaseWidgetProps, WidgetStatus } from '@/types/widget';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

function getStatusStyles(status: WidgetStatus | undefined): string {
  switch (status) {
    case 'good':
      return 'border-green-200 bg-green-50/50 dark:bg-green-950/20';
    case 'warning':
      return 'border-amber-200 bg-amber-50/50 dark:bg-amber-950/20';
    case 'critical':
      return 'border-red-200 bg-red-50/50 dark:bg-red-950/20';
    default:
      return '';
  }
}

export function WidgetShell({
  title,
  status = 'neutral',
  loading,
  error,
  empty,
  actions,
  onRefresh,
  children,
}: BaseWidgetProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Unable to load {title}</AlertTitle>
        <AlertDescription className="mt-2 space-y-2">
          <p>{error.message || 'An unexpected error occurred'}</p>
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              className="mt-2"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  // Empty state
  if (empty) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No data available yet.</p>
        </CardContent>
      </Card>
    );
  }

  // Success state
  return (
    <Card className={getStatusStyles(status)}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center justify-between">
          <span>{title}</span>
          {actions && actions.length > 0 && actions[0].href && (
            <a
              href={actions[0].href}
              className="text-xs text-primary hover:underline"
            >
              See all →
            </a>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}