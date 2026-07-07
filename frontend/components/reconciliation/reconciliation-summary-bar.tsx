'use client'

import { RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { usePendingReconciliations, useReconciliations } from '@/lib/hooks/use-reconciliation'

export function ReconciliationSummaryBar() {
  const { data: allData } = useReconciliations()
  const { data: pendingData, refetch: refetchPending } = usePendingReconciliations()

  const pendingCount = pendingData?.reconciliations?.length ?? 0
  const confirmedCount = allData?.reconciliations?.filter(r => r.status === 'confirmed').length ?? 0
  const rejectedCount = allData?.reconciliations?.filter(r => r.status === 'rejected').length ?? 0

  const handleScan = () => {
    refetchPending()
  }

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-muted/30 rounded-lg">
      <div className="flex items-center gap-4 text-sm">
        <div>
          <span className="text-muted-foreground">Pending Review:</span>
          <span className="font-semibold ml-1">{pendingCount}</span>
        </div>
        <div className="text-muted-foreground">|</div>
        <div>
          <span className="text-muted-foreground">Confirmed:</span>
          <span className="font-semibold ml-1">{confirmedCount}</span>
        </div>
        <div className="text-muted-foreground">|</div>
        <div>
          <span className="text-muted-foreground">Rejected:</span>
          <span className="font-semibold ml-1">{rejectedCount}</span>
        </div>
      </div>
      
      <Button 
        variant="outline" 
        size="sm"
        onClick={handleScan}
      >
        <RefreshCw className="mr-2 h-4 w-4" />
        Scan for New Matches
      </Button>
    </div>
  )
}