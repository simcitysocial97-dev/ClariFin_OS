/**
 * Audit Trail - Stage 4 Reconciliation Intelligence Workspace
 *
 * Displays the audit trail of reconciliation actions.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, CheckCircle, XCircle, AlertTriangle, User } from 'lucide-react';
import type { AuditTrailEntryViewModel } from '@/types/reconciliation-view-model';

/**
 * Audit Trail Props
 */
interface AuditTrailProps {
  auditTrail: AuditTrailEntryViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Get action icon
 */
function getActionIcon(action: string) {
  switch (action) {
    case 'confirm':
    case 'reconcile':
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'reject':
      return <XCircle className="h-4 w-4 text-red-600" />;
    case 'dispute':
      return <AlertTriangle className="h-4 w-4 text-amber-600" />;
    default:
      return <AlertCircle className="h-4 w-4 text-gray-600" />;
  }
}

/**
 * Get action badge class
 */
function getActionBadgeClass(action: string) {
  switch (action) {
    case 'confirm':
    case 'reconcile':
      return 'bg-green-100 text-green-800';
    case 'reject':
      return 'bg-red-100 text-red-800';
    case 'dispute':
      return 'bg-amber-100 text-amber-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Audit Trail Component
 *
 * Shows a timeline of reconciliation actions with user, action type, and timestamp.
 */
export function AuditTrail({ auditTrail, loading, error }: AuditTrailProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load audit trail</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!auditTrail || auditTrail.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No audit trail entries found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit Trail ({auditTrail.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {auditTrail.map((entry) => (
            <div key={entry.id} className="flex items-start gap-3 p-3 border rounded-lg hover:bg-gray-50">
              <div className="flex-shrink-0 mt-0.5">
                {getActionIcon(entry.action)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-1 rounded-full ${getActionBadgeClass(entry.action)}`}>
                    {entry.action}
                  </span>
                  <span className="text-xs text-gray-500">
                    Transaction #{entry.transaction_id}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-600">
                  <User className="h-3 w-3" />
                  <span>{entry.user}</span>
                  <span>•</span>
                  <span>{formatTimestamp(entry.timestamp)}</span>
                </div>
                {entry.notes && (
                  <p className="text-xs text-gray-500 mt-1 truncate">
                    {entry.notes}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}