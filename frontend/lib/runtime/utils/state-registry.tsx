/**
 * State Registry - Icon and configuration mapping for runtime states
 *
 * Uses a registry pattern instead of switch statements for extensibility.
 */

import type { RuntimeState } from '../contracts/runtime-state'
import { Loader2, AlertCircle, Inbox, WifiOff, ShieldX, Clock } from 'lucide-react'
import type { ReactNode } from 'react'

/**
 * State configuration registry
 * Maps each runtime state to its icon, default title, and description
 */
export const stateRegistry: Record<
  RuntimeState,
  {
    icon: ReactNode
    defaultTitle: string
    defaultDescription: string
    color: string
  }
> = {
  loading: {
    icon: <Loader2 className="h-8 w-8 animate-spin" />,
    defaultTitle: 'Loading',
    defaultDescription: 'Fetching your data...',
    color: 'text-blue-500',
  },
  success: {
    icon: null,
    defaultTitle: '',
    defaultDescription: '',
    color: '',
  },
  empty: {
    icon: <Inbox className="h-8 w-8" />,
    defaultTitle: 'No data available',
    defaultDescription: 'There is nothing to display right now.',
    color: 'text-muted-foreground',
  },
  error: {
    icon: <AlertCircle className="h-8 w-8" />,
    defaultTitle: 'Something went wrong',
    defaultDescription: 'An error occurred while loading your data.',
    color: 'text-red-500',
  },
  offline: {
    icon: <WifiOff className="h-8 w-8" />,
    defaultTitle: 'You are offline',
    defaultDescription: 'Check your connection and try again.',
    color: 'text-amber-500',
  },
  permission: {
    icon: <ShieldX className="h-8 w-8" />,
    defaultTitle: 'Access denied',
    defaultDescription: 'You do not have permission to view this data.',
    color: 'text-red-500',
  },
  stale: {
    icon: <Clock className="h-8 w-8" />,
    defaultTitle: 'Updating',
    defaultDescription: 'Refreshing your data...',
    color: 'text-blue-500',
  },
}

/**
 * Get state configuration from registry
 */
export function getStateConfig(state: RuntimeState) {
  return stateRegistry[state]
}

/**
 * Get icon for a state
 */
export function getStateIcon(state: RuntimeState): ReactNode {
  return stateRegistry[state].icon
}

/**
 * Get color for a state
 */
export function getStateColor(state: RuntimeState): string {
  return stateRegistry[state].color
}