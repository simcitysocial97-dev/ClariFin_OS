'use client'

import { ReconciliationMatchCard } from '@/components/reconciliation/reconciliation-match-card'
import { ReconciliationSummaryBar } from '@/components/reconciliation/reconciliation-summary-bar'
import { ReconciliationEmptyState } from '@/components/reconciliation/reconciliation-empty-state'
import { usePendingReconciliations } from '@/lib/hooks/use-reconciliation'

export default function ReconciliationPage() {
  const { data, loading, error } = usePendingReconciliations()

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">Reconciliation</h1>
        <p>Loading pending matches...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">Reconciliation</h1>
        <p className="text-red-500">Error loading reconciliations: {error.message}</p>
      </div>
    )
  }

  const matches = data?.reconciliations ?? []

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Reconciliation</h1>
      
      <div className="space-y-4">
        <ReconciliationSummaryBar />
        
        {matches.length === 0 ? (
          <ReconciliationEmptyState />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {matches.map((match) => (
              <ReconciliationMatchCard key={match.id} match={match} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}