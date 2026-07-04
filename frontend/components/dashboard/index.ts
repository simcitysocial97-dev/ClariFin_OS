/**
 * Dashboard Components Index
 * ==========================
 * 
 * Export all dashboard widget components for easy importing.
 */

export { BentoGridLayout, BentoGridItem } from "./bento-grid-layout";
export { WidgetErrorFallback } from "./widget-error-fallback";
export {
  MetricCardSkeleton,
  MetricsRowSkeleton,
  ChartWidgetSkeleton,
  ListWidgetSkeleton,
  DonutChartSkeleton,
  AreaChartSkeleton,
} from "./skeletons";

export { MetricsRow } from "./metrics-row";
export { CashflowChartWidget } from "./cashflow-chart-widget";
export { UpcomingPaymentsWidget } from "./upcoming-payments-widget";
export { AssetAllocationWidget } from "./asset-allocation-widget";
export { ActiveLoansWidget } from "./active-loans-widget";
export { InvestmentsWidget } from "./investments-widget";
export { NetWorthTrendWidget } from "./networth-trend-widget";

// Re-export existing components
export { RecentTransactions } from "./recent-transactions";
export { QuickStats } from "./quick-stats";
export { InsightCards } from "./insight-cards";
export { SpendingOverview } from "./spending-overview";
