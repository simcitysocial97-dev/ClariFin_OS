/**
 * Widget Types - Single Source of Truth for Widget Contracts
 * 
 * Every widget in the Financial OS must conform to this interface.
 */

import type { ReactNode } from 'react';

// Widget status types - used for color coding and user perception
export type WidgetStatus = 'good' | 'warning' | 'critical' | 'neutral';

// Actions that can be triggered from widgets
export interface WidgetAction {
  label: string;
  href?: string;
  onClick?: () => void;
}

// Query state wrapper for consistent loading/error handling
export interface WidgetQueryState<T> {
  data?: T | null;
  isLoading: boolean;
  error?: Error | null;
  refetch?: () => void;
}

// Base widget props - all widgets must accept these
export interface BaseWidgetProps {
  title: string;
  status?: WidgetStatus;
  loading?: boolean;
  error?: Error | null;
  empty?: boolean;
  drilldownRoute?: string;
  actions?: WidgetAction[];
  onRefresh?: () => void;
  children?: ReactNode;
}

// Widget grid layout props
export interface WidgetGridProps {
  columns?: 1 | 2 | 3 | 4;
  className?: string;
}

// Section header props
export interface WidgetSectionProps {
  title: string;
  description?: string;
  actionHref?: string;
  actionLabel?: string;
}