/**
 * Command Center Page - reads workspace, selection, timeline, navigation state from runtime.
 */

'use client';

import { useEffect } from 'react';
import { commandCenterRuntime } from '@/lib/command-center';
import { CommandCenterLayout } from '@/components/command-center';
import { useDashboardMetrics } from '@/lib/hooks/use-dashboard-metrics';
import { useAccountsCapability } from '@/lib/capabilities/use-accounts-capability';
import { useLoansCapability } from '@/lib/capabilities/use-loans-capability';
import { useCreditCardsCapability } from '@/lib/capabilities/use-credit-cards-capability';
import { useInvestmentsCapability } from '@/lib/capabilities/use-investments-capability';
import { useCashflowCapability } from '@/lib/capabilities/use-cashflow-capability';
import { useBehaviourCapability } from '@/lib/capabilities/use-behaviour-capability';
import { useReconciliationCapability } from '@/lib/capabilities/use-reconciliation-capability';
import { useForecastCapability } from '@/lib/capabilities/use-forecast-capability';
import { useNavigation } from '@/lib/runtime';

export default function CommandCenterPage() {
  const { pushPath } = useNavigation();
  const { data: dashboardData } = useDashboardMetrics();
  const { accounts: accountsData } = useAccountsCapability();
  const { loans: loansData } = useLoansCapability();
  const { creditCards: cardsData } = useCreditCardsCapability();
  const { investments: investmentsData } = useInvestmentsCapability();
  const { cashflow: cashflowData } = useCashflowCapability();
  const { behaviour: behaviourData } = useBehaviourCapability();
  const { reconciliation: reconciliationData } = useReconciliationCapability();
  const { forecast } = useForecastCapability();

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
      forecast: forecast,
      reconciliation: reconciliationData,
    };

    if (Object.values(viewModels).some(v => v !== undefined)) {
      commandCenterRuntime.build(viewModels);
    }
  }, [pushPath, dashboardData, accountsData, loansData, cardsData, investmentsData, cashflowData, behaviourData, forecast, reconciliationData]);

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
        forecast: forecast,
        reconciliation: reconciliationData,
      }}
    />
  );
}
