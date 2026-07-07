'use client'

import { CheckCircle2 } from 'lucide-react'

export function ReconciliationEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
        <CheckCircle2 className="h-8 w-8 text-green-600" />
      </div>
      <h3 className="text-lg font-semibold mb-2">All transfers accounted for</h3>
      <p className="text-sm text-muted-foreground max-w-sm">
        No pending transfer matches found. All cross-account transfers have been reviewed.
      </p>
    </div>
  )
}