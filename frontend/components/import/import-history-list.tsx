'use client';

import { FileText, Clock, CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { useStatements } from '@/lib/hooks/use-finance-data';
import type { Statement } from '@/lib/api/client';

// Status type based on validation_status from backend
type ImportStatus = 'success' | 'failed' | 'partial' | 'pending';

const statusConfig: Record<ImportStatus, {
  icon: typeof CheckCircle;
  label: string;
  variant: 'default' | 'destructive' | 'secondary' | 'outline';
  className: string;
}> = {
  success: {
    icon: CheckCircle,
    label: 'Success',
    variant: 'default',
    className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  },
  failed: {
    icon: XCircle,
    label: 'Failed',
    variant: 'destructive',
    className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  },
  partial: {
    icon: AlertTriangle,
    label: 'Partial',
    variant: 'secondary',
    className: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300',
  },
  pending: {
    icon: Clock,
    label: 'Pending',
    variant: 'outline',
    className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  },
};

/**
 * Map backend validation_status to our ImportStatus
 */
function mapValidationStatus(validationStatus: string | undefined): ImportStatus {
  if (!validationStatus || validationStatus === 'pending') return 'pending';
  if (validationStatus === 'valid') return 'success';
  if (validationStatus === 'invalid') return 'failed';
  if (validationStatus === 'partial') return 'partial';
  return 'success';
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
}

interface ImportHistoryListProps {
  maxItems?: number;
}

export function ImportHistoryList({ maxItems = 10 }: ImportHistoryListProps) {
  const { statements, loading, error } = useStatements();
  const items: Statement[] = statements || [];
  const displayItems = items.slice(0, maxItems);

  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Recent Imports
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm">Loading import history...</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state - non-blocking, show error but don't prevent import wizard
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Recent Imports
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive" className="text-sm">
            <AlertDescription>
              Failed to load import history. You can still import files.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Recent Imports
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px]">
          <div className="space-y-3">
            {displayItems.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No import history yet</p>
                <p className="text-xs mt-1">Upload your first statement to see it here</p>
              </div>
            ) : (
              displayItems.map((item: Statement) => {
                const status = mapValidationStatus(item.validation_status);
                const statusConfigItem = statusConfig[status];
                const StatusIcon = statusConfigItem.icon;

                return (
                  <div
                    key={item.id}
                    className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                  >
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <FileText className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium truncate">{item.file_name}</p>
                        <Badge
                          variant={statusConfigItem.variant}
                          className={cn('text-xs', statusConfigItem.className)}
                        >
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {statusConfigItem.label}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                        <span>{item.bank}</span>
                        <span>•</span>
                        <span>{formatRelativeTime(item.imported_at)}</span>
                      </div>
                      {item.transaction_count > 0 && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {item.transaction_count} transactions imported
                        </p>
                      )}
                      {item.validation_status === 'invalid' && item.validation_difference !== 0 && (
                        <p className="text-xs text-destructive mt-1">
                          Validation failed (diff: ₹{(item.validation_difference / 100).toFixed(2)})
                        </p>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
