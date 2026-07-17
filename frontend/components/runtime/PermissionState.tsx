/**
 * PermissionState - Generic permission denied state
 */

import { ShieldX } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface PermissionStateProps {
  title?: string
  description?: string
  className?: string
}

export function PermissionState({
  title = 'Access denied',
  description = 'You do not have permission to view this data.',
  className,
}: PermissionStateProps) {
  return (
    <Card className={cn('border-destructive/50', className)}>
      <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
        <ShieldX className="h-12 w-12 text-destructive mb-4" aria-hidden="true" />

        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground max-w-md">{description}</p>
      </CardContent>
    </Card>
  )
}