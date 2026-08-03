/**
 * Command Center Page - reads workspace, selection, timeline, navigation state from runtime.
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
import { useNavigation } from '@/lib/runtime';

export default function CommandCenterPage() {
  const { pushPath } = useNavigation();
  const { data: dashboardData } = useDashboardMetrics();
  const { data: accountsData } = useManagedAccounts();
  const { data: loansData } = useLoans();
  const { data: cardsData } = useCards();
  const { data: investmentsData } = useInvestments();
  const { data: cashflowData } = useCashflow();
  const { data: behaviourData } = useBehaviorScore();
  const { data: reconciliationData } = useReconciliations();

  useEffect(() => {
    pushPath('/command-center', 'command-center');

    const viewModels: Record<string, unknown> = {
      transactions: { transactions: dashboardData?.recent_transactions ?? [] },
      accounts: accountsData,
      loans: loansData,
      cards: cardsData,
      investments: investmentsData,
      cashflow: cashflowData,
      behaviour: behaviourData,
      forecast: cashflowData,
      reconciliation: reconciliationData,
    };

    if (Object.values(viewModels).some(v => v !== undefined)) {
      commandCenterRuntime.build(viewModels);
    }
  }, [pushPath, dashboardData, accountsData, loansData, cardsData, investmentsData, cashflowData, behaviourData, reconciliationData]);

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
        forecast: cashflowData,
        reconciliation: reconciliationData,
      }}
    />
  );
}
