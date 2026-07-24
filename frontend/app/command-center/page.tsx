/**
 * Command Center Page - Stage 8E-B Command Center
 *
 * Main entry point for the Command Center workspace.
 * Three-layer analytical surface: Graph, Decision Feed, Metrics Strip.
 *
 * Architecture:
 *   Top Command Bar (global)
 *   ┌──────────────────────────────────────────────────────────┬───────────────┐
 *   │                                                          │               │
 *   │                 Financial Graph                          │ Decision Feed │
 *   │                                                          │               │
 *   ├──────────────────────────────────────────────────────────┴───────────────┤
 *   │ Metrics Strip                                                           │
 *   └──────────────────────────────────────────────────────────────────────────┘
 *   Right Inspector (global)
 *   Bottom Timeline (global)
 */

'use client';

import { useEffect } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import { CommandCenterLayout } from '@/components/command-center';
import { useDashboardMetrics } from '@/lib/hooks/use-dashboard-metrics';
import { useManagedAccounts } from '@/lib/hooks/use-accounts';
import { useLoans } from '@/lib/hooks/use-loans';
import { useCards } from '@/lib/hooks/use-cards';
import { useInvestments } from '@/lib/hooks/use-investments';
import { useCashflow } from '@/lib/hooks/use-cashflow';
import { useBehaviorScore } from '@/lib/hooks/use-behavior-score';
import { useReconciliations } from '@/lib/hooks/use-reconciliation';

// ===== Page Component =====
export default function CommandCenterPage() {
  // Load all workspace data
  const { data: dashboardData } = useDashboardMetrics();
  const { data: accountsData } = useManagedAccounts();
  const { data: loansData } = useLoans();
  const { data: cardsData } = useCards();
  const { data: investmentsData } = useInvestments();
  const { data: cashflowData } = useCashflow();
  const { data: behaviourData } = useBehaviorScore();
  const { data: forecastData } = useCashflow(); // Use cashflow as forecast placeholder
  const { data: reconciliationData } = useReconciliations();

  // Build graph when data is available
  useEffect(() => {
    const viewModels: Record<string, unknown> = {
      transactions: { transactions: dashboardData?.recent_transactions ?? [] },
      accounts: accountsData,
      loans: loansData,
      cards: cardsData,
      investments: investmentsData,
      cashflow: cashflowData,
      behaviour: behaviourData,
      forecast: forecastData,
      reconciliation: reconciliationData,
    };

    // Only build if we have at least some data
    if (Object.values(viewModels).some(v => v !== undefined)) {
      commandCenterRuntime.build(viewModels);
    }
  }, [
    dashboardData,
    accountsData,
    loansData,
    cardsData,
    investmentsData,
    cashflowData,
    behaviourData,
    forecastData,
    reconciliationData,
  ]);

  return (
    <CommandCenterLayout
      viewModels={{
        transactions: { transactions: dashboardData?.recent_transactions ?? [] },
        accounts: accountsData,
        loans: loansData,
        cards: cardsData,
        investments: investmentsData,
        cashflow: cashflowData,
        behaviour: behaviourData,
        forecast: forecastData,
        reconciliation: reconciliationData,
      }}
    />
  );
}