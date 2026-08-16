/**
 * Context Panel - Stage 9 Context Panel Experience
 *
 * The Context Panel is the OS's inspector. It displays contextual
 * information about the currently selected entity without any navigation.
 *
 * Architecture: SelectionRuntime → ContextPanel → Entity-specific context views
 *
 * Sections: Accounts → Transactions → Loans → Evidence → Insights → Forecast → Actions → Explanation
 */

'use client';

import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { formatINR, formatDateDisplay } from '@/lib/utils/format';
import { selectionRuntime } from '@/lib/runtime/selection-runtime';
import { passiveInsightRuntime } from '@/lib/intelligence/passive-runtime';
import type { PassiveInsight } from '@/lib/intelligence/passive-runtime';
import { investigativeInsightRuntime } from '@/lib/intelligence/investigative-runtime';
import { Surface } from '@/components/primitives/surface/surface';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { FinancialBadge } from '@/components/primitives/badge-semantic/financial-badge';
import { ScrollRegion } from '@/components/primitives/layout/scroll-region';
import { Stack } from '@/components/primitives/layout/stack';
import type { SelectionEntity } from '@/lib/runtime/runtime-types';
import { GraphContextPanel } from '@/components/graph/graph-context-panel';
import { useTransactionCapability } from '@/lib/capabilities/use-transaction-capability';
import { useAccountsCapability } from '@/lib/capabilities/use-accounts-capability';
import { useLoansCapability } from '@/lib/capabilities/use-loans-capability';
import { useCreditCardsCapability } from '@/lib/capabilities/use-credit-cards-capability';
import { useInvestmentsCapability } from '@/lib/capabilities/use-investments-capability';
import { useReconciliationCapability } from '@/lib/capabilities/use-reconciliation-capability';

// ===== Severity Color Mapping =====
const severityColors: Record<string, string> = {
  info: 'text-[var(--color-info-500)]',
  warning: 'text-[var(--color-warning-500)]',
  critical: 'text-[var(--color-negative-500)]',
  positive: 'text-[var(--color-positive-500)]',
};

const severityBg: Record<string, string> = {
  info: 'bg-[var(--color-info-50)] dark:bg-[var(--color-info-950)]',
  warning: 'bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-950)]',
  critical: 'bg-[var(--color-negative-50)] dark:bg-[var(--color-negative-950)]',
  positive: 'bg-[var(--color-positive-50)] dark:bg-[var(--color-positive-950)]',
};

// ===== Section Components =====

interface InspectorSectionProps {
  title: string;
  icon?: string;
  children: React.ReactNode;
  className?: string;
}

function InspectorSection({ title, icon, children, className }: InspectorSectionProps) {
  return (
    <Surface variant="raised" density="compact" className={cn('border-0 border-b border-[var(--border-subtle)] last:border-b-0', className)}>
      <div className="flex items-center gap-1.5 px-2 py-1 border-b border-[var(--border-subtle)]">
        {icon && <FinancialIcon name={icon} size={10} className="text-[var(--text-tertiary)]" />}
        <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">{title}</span>
      </div>
      <div className="px-2 py-1.5 space-y-1">
        {children}
      </div>
    </Surface>
  );
}

// ===== Empty State with Passive Insights =====
interface EmptyContextStateProps {
  insights: PassiveInsight[];
  onDismiss?: (id: string) => void;
}

function EmptyContextState({ insights, onDismiss }: EmptyContextStateProps) {
  return (
    <div className="flex flex-col gap-2 px-2 py-2">
      {insights.length > 0 ? (
        <>
          <div className="flex items-center gap-1.5 px-1 py-1 border-b border-[var(--border-subtle)] mb-1">
            <FinancialIcon name="behaviour" size={10} className="text-[var(--text-tertiary)]" />
            <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
              Active Insights
            </span>
            <span className="fin-caption text-[var(--text-tertiary)] ml-auto">{insights.length}/5</span>
          </div>
          {insights.map((insight) => (
            <div
              key={insight.id}
              className={cn(
                'flex items-center gap-1.5 px-1.5 py-1 rounded-[var(--radius-sm)]',
                severityBg[insight.severity] ?? 'bg-[var(--surface-raised)]',
              )}
            >
              <span className={cn('fin-caption', severityColors[insight.severity] ?? 'text-[var(--text-tertiary)]')}>
                ·
              </span>
              <div className="min-w-0 flex-1">
                <span className="fin-caption font-medium text-[var(--text-primary)] truncate">{insight.title}</span>
                {!onDismiss && (
                  <span className="fin-caption text-[var(--text-secondary)] block truncate">{insight.summary}</span>
                )}
              </div>
              {insight.dismissible && onDismiss && (
                <button
                  onClick={() => onDismiss(insight.id)}
                  className="shrink-0 h-4 w-4 rounded-full flex items-center justify-center hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] transition-colors"
                  aria-label="Dismiss insight"
                >
                  <span className="text-[8px] leading-none">×</span>
                </button>
              )}
            </div>
          ))}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center h-full gap-2 px-4 py-6 text-center">
          <FinancialIcon name="search" size={24} className="text-[var(--text-tertiary)] opacity-50" />
          <p className="fin-body text-[var(--text-secondary)]">Select an entity to view context</p>
          <p className="fin-caption text-[var(--text-tertiary)]">
            Click any row or card in the workspace to inspect
          </p>
        </div>
      )}
    </div>
  );
}

// ===== Account Context =====
interface AccountContextProps {
  entity: SelectionEntity;
}

function AccountContext({ entity }: AccountContextProps) {
  const { accounts, loading } = useAccountsCapability();
  const account = useMemo(() =>
    accounts?.accounts.find(a => a.id === String(entity.id)),
    [accounts, entity.id]
  );

  if (loading && !account) {
    return (
      <InspectorSection title="Account" icon="wallet">
        <p className="fin-body-small text-[var(--text-tertiary)]">Loading account data...</p>
      </InspectorSection>
    );
  }

  if (!account) {
    return (
      <InspectorSection title="Account" icon="wallet">
        <p className="fin-body-small text-[var(--text-secondary)]">
          Account not found in current view. Open the Accounts workspace to load data.
        </p>
      </InspectorSection>
    );
  }

  return (
    <>
      <InspectorSection title="Account" icon="wallet">
        <Stack gap={1}>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Status</span>
            <FinancialBadge semantic={account.status === 'active' ? 'positive' : 'neutral'} variant="ghost" className="text-[9px] px-1">
              {account.status}
            </FinancialBadge>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Balance</span>
            <span className="fin-mono font-medium">{formatINR(account.balance_paise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Institution</span>
            <span className="fin-body text-[var(--text-primary)]">{account.institution}</span>
          </div>
          {account.opened_date && (
            <div className="flex items-center justify-between">
              <span className="fin-caption text-[var(--text-secondary)]">Opened</span>
              <span className="fin-body text-[var(--text-primary)]">{formatDateDisplay(account.opened_date)}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Type</span>
            <span className="fin-body text-[var(--text-primary)]">{account.type}</span>
          </div>
        </Stack>
      </InspectorSection>

      <InspectorSection title="Explanation" icon="evidence">
        <p className="fin-body-small text-[var(--text-secondary)]">
          {account.name} with current balance of {formatINR(account.balance_paise)} at {account.institution}.
        </p>
      </InspectorSection>
    </>
  );
}

// ===== Transaction Context =====
interface TransactionContextProps {
  entity: SelectionEntity;
}

function TransactionContext({ entity }: TransactionContextProps) {
  const { transactions, loading } = useTransactionCapability();
  const transaction = useMemo(() =>
    transactions.find(t => t.id === String(entity.id)),
    [transactions, entity.id]
  );

  if (loading && !transaction) {
    return (
      <InspectorSection title="Transaction" icon="receipt">
        <p className="fin-body-small text-[var(--text-tertiary)]">Loading transaction data...</p>
      </InspectorSection>
    );
  }

  if (!transaction) {
    return (
      <InspectorSection title="Transaction" icon="receipt">
        <p className="fin-body-small text-[var(--text-secondary)]">
          Transaction not found in current view. Open the Transactions workspace to load data.
        </p>
      </InspectorSection>
    );
  }

  return (
    <>
      <InspectorSection title="Transaction" icon="receipt">
        <Stack gap={1}>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Amount</span>
            <span className={cn('fin-mono font-semibold', transaction.amount.paise < 0 ? 'text-[var(--color-negative-500)]' : 'text-[var(--color-positive-500)]')}>
              {formatINR(transaction.amount.paise)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Description</span>
            <span className="fin-body text-[var(--text-primary)]">{transaction.description}</span>
          </div>
          {transaction.category_name && (
            <div className="flex items-center justify-between">
              <span className="fin-caption text-[var(--text-secondary)]">Category</span>
              <FinancialBadge semantic="info" variant="ghost" className="text-[9px] px-1">
                {transaction.category_path || transaction.category_name}
              </FinancialBadge>
            </div>
          )}
          {transaction.merchant_name && (
            <div className="flex items-center justify-between">
              <span className="fin-caption text-[var(--text-secondary)]">Merchant</span>
              <span className="fin-body text-[var(--text-primary)]">{transaction.merchant_name}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Date</span>
            <span className="fin-body text-[var(--text-primary)]">{formatDateDisplay(transaction.date)}</span>
          </div>
        </Stack>
      </InspectorSection>

      <InspectorSection title="Evidence" icon="evidence">
        <Stack gap={1}>
          {transaction.evidence?.map((ev, i) => (
            <div key={i} className="flex items-start gap-1.5">
              <FinancialBadge semantic="info" variant="ghost" className="text-[8px] px-1 shrink-0 mt-0.5">{ev.type}</FinancialBadge>
              <span className="fin-caption text-[var(--text-secondary)]">{ev.summary}</span>
            </div>
          )) ?? (
            <span className="fin-caption text-[var(--text-tertiary)]">No evidence available</span>
          )}
        </Stack>
      </InspectorSection>

      <InspectorSection title="Explanation" icon="evidence">
        <p className="fin-body-small text-[var(--text-secondary)]">
          {transaction.category_path
            ? `Categorized as ${transaction.category_path} based on historical merchant patterns.`
            : 'No categorization explanation available.'}
        </p>
      </InspectorSection>
    </>
  );
}

// ===== Loan Context =====
interface LoanContextProps {
  entity: SelectionEntity;
}

function LoanContext({ entity }: LoanContextProps) {
  const { loans, loading } = useLoansCapability();
  const loan = useMemo(() =>
    loans?.loans.find(l => l.id === String(entity.id)),
    [loans, entity.id]
  );

  if (loading && !loan) {
    return (
      <InspectorSection title="Loan" icon="loan">
        <p className="fin-body-small text-[var(--text-tertiary)]">Loading loan data...</p>
      </InspectorSection>
    );
  }

  if (!loan) {
    return (
      <InspectorSection title="Loan" icon="loan">
        <p className="fin-body-small text-[var(--text-secondary)]">
          Loan not found in current view. Open the Loans workspace to load data.
        </p>
      </InspectorSection>
    );
  }

  const paid_principal_paise = loan.original_amount_paise - loan.outstanding_paise;
  const paid_interest_paise = (loan.emi_paise * loan.remaining_months) - paid_principal_paise;

  return (
    <>
      <InspectorSection title="Loan" icon="loan">
        <Stack gap={1}>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Outstanding</span>
            <span className="fin-mono font-semibold">{formatINR(loan.outstanding_paise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Monthly EMI</span>
            <span className="fin-mono">{formatINR(loan.emi_paise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Interest Rate</span>
            <span className="fin-body text-[var(--text-primary)]">{(loan.interest_rate_bps / 100).toFixed(2)}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Remaining</span>
            <span className="fin-body text-[var(--text-primary)]">{loan.remaining_months} months</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Lender</span>
            <span className="fin-body text-[var(--text-primary)]">{loan.lender}</span>
          </div>
        </Stack>
      </InspectorSection>

      <InspectorSection title="Forecast" icon="forecast">
        <Stack gap={1}>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Paid (Principal)</span>
            <span className="fin-mono text-[var(--color-positive-600)]">{formatINR(paid_principal_paise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Paid (Interest)</span>
            <span className="fin-mono text-[var(--color-negative-600)]">{formatINR(Math.max(0, paid_interest_paise))}</span>
          </div>
        </Stack>
      </InspectorSection>

      <InspectorSection title="Explanation" icon="evidence">
        <p className="fin-body-small text-[var(--text-secondary)]">
          {loan.name} with {loan.remaining_months} months remaining at {(loan.interest_rate_bps / 100).toFixed(2)}% interest. Principal portion increasing as amortization progresses.
        </p>
      </InspectorSection>
    </>
  );
}

// ===== Card Context =====
interface CardContextProps {
  entity: SelectionEntity;
}

function CardContext({ entity }: CardContextProps) {
  const { creditCards, loading } = useCreditCardsCapability();
  const card = useMemo(() =>
    creditCards?.cards.find(c => c.id === String(entity.id)),
    [creditCards, entity.id]
  );

  if (loading && !card) {
    return (
      <InspectorSection title="Card" icon="credit-card">
        <p className="fin-body-small text-[var(--text-tertiary)]">Loading card data...</p>
      </InspectorSection>
    );
  }

  if (!card) {
    return (
      <InspectorSection title="Card" icon="credit-card">
        <p className="fin-body-small text-[var(--text-secondary)]">
          Card not found in current view. Open the Credit Cards workspace to load data.
        </p>
      </InspectorSection>
    );
  }

  const utilization = Math.round((card.current_balance_paise / card.credit_limit_paise) * 100);

  return (
    <>
      <InspectorSection title="Card" icon="credit-card">
        <Stack gap={1}>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Card</span>
            <span className="fin-body text-[var(--text-primary)]">{card.name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Last 4</span>
            <span className="fin-mono">{card.card_number_last4}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Current Usage</span>
            <span className="fin-mono font-semibold">{formatINR(card.current_balance_paise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Credit Limit</span>
            <span className="fin-mono">{formatINR(card.credit_limit_paise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Utilization</span>
            <div className="flex items-center gap-1.5">
              <div className="w-12 h-1.5 bg-[var(--color-neutral-200)] rounded-full overflow-hidden">
                <div
                  className={cn('h-full rounded-full', utilization > 80 ? 'bg-[var(--color-negative-500)]' : 'bg-[var(--color-positive-500)]')}
                  style={{ width: `${Math.min(utilization, 100)}%` }}
                />
              </div>
              <span className="fin-caption text-[var(--text-tertiary)]">{utilization}%</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Due Date</span>
            <span className="fin-body text-[var(--text-primary)]">{formatDateDisplay(card.due_date)}</span>
          </div>
        </Stack>
      </InspectorSection>

      <InspectorSection title="Explanation" icon="evidence">
        <p className="fin-body-small text-[var(--text-secondary)]">
          Credit utilization at {utilization}% — {utilization > 80 ? 'above' : 'within'} healthy range. Payment due on {formatDateDisplay(card.due_date)}.
        </p>
      </InspectorSection>
    </>
  );
}

// ===== Investment Context =====
interface InvestmentContextProps {
  entity: SelectionEntity;
}

function InvestmentContext({ entity }: InvestmentContextProps) {
  const { investments, loading } = useInvestmentsCapability();
  const investment = useMemo(() =>
    investments?.investments.find(i => i.id === String(entity.id)),
    [investments, entity.id]
  );

  if (loading && !investment) {
    return (
      <InspectorSection title="Investment" icon="investment">
        <p className="fin-body-small text-[var(--text-tertiary)]">Loading investment data...</p>
      </InspectorSection>
    );
  }

  if (!investment) {
    return (
      <InspectorSection title="Investment" icon="investment">
        <p className="fin-body-small text-[var(--text-secondary)]">
          Investment not found in current view. Open the Investments workspace to load data.
        </p>
      </InspectorSection>
    );
  }

  const gain_paise = investment.current_value_paise - investment.invested_paise;
  const gain_pct = investment.invested_paise > 0 ? ((gain_paise / investment.invested_paise) * 100).toFixed(1) : '0.0';

  return (
    <>
      <InspectorSection title="Investment" icon="investment">
        <Stack gap={1}>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Scheme</span>
            <span className="fin-body text-[var(--text-primary)]">{investment.name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Type</span>
            <FinancialBadge semantic="info" variant="ghost" className="text-[9px] px-1">{investment.type}</FinancialBadge>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Institution</span>
            <span className="fin-body text-[var(--text-primary)]">{investment.institution}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Current Value</span>
            <span className="fin-mono font-semibold">{formatINR(investment.current_value_paise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Invested</span>
            <span className="fin-mono">{formatINR(investment.invested_paise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Gain</span>
            <span className={cn('fin-mono font-semibold', gain_paise >= 0 ? 'text-[var(--color-positive-500)]' : 'text-[var(--color-negative-500)]')}>
              {gain_paise >= 0 ? '+' : ''}{formatINR(gain_paise)} ({gain_pct}%)
            </span>
          </div>
        </Stack>
      </InspectorSection>

      <InspectorSection title="Explanation" icon="evidence">
        <p className="fin-body-small text-[var(--text-secondary)]">
          {investment.name} with current value of {formatINR(investment.current_value_paise)} against an investment of {formatINR(investment.invested_paise)}.
        </p>
      </InspectorSection>
    </>
  );
}

// ===== Reconciliation Context =====
interface ReconciliationContextProps {
  entity: SelectionEntity;
}

function ReconciliationContext({ entity }: ReconciliationContextProps) {
  const { reconciliation, loading } = useReconciliationCapability();
  const statement = useMemo(() =>
    reconciliation?.statements.find(s => String(s.statement_id) === String(entity.id)),
    [reconciliation, entity.id]
  );

  if (loading && !statement) {
    return (
      <InspectorSection title="Reconciliation" icon="check-square">
        <p className="fin-body-small text-[var(--text-tertiary)]">Loading reconciliation data...</p>
      </InspectorSection>
    );
  }

  if (!statement) {
    return (
      <InspectorSection title="Reconciliation" icon="check-square">
        <p className="fin-body-small text-[var(--text-secondary)]">
          Reconciliation not found in current view. Open the Reconciliation workspace to load data.
        </p>
      </InspectorSection>
    );
  }

  const unmatched_count = statement.transaction_count - statement.reconciled_count;

  return (
    <>
      <InspectorSection title="Reconciliation" icon="check-square">
        <Stack gap={1}>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Period</span>
            <span className="fin-body text-[var(--text-primary)]">{statement.period_from} — {statement.period_to}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Bank</span>
            <span className="fin-body text-[var(--text-primary)]">{statement.bank}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Transactions</span>
            <span className="fin-mono text-[var(--color-positive-600)]">{statement.transaction_count}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Reconciled</span>
            <span className="fin-mono text-[var(--color-positive-600)]">{statement.reconciled_count}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Unreconciled</span>
            <span className="fin-mono text-[var(--color-warning-600)]">{unmatched_count}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="fin-caption text-[var(--text-secondary)]">Status</span>
            <FinancialBadge semantic={statement.status === 'confirmed' ? 'positive' : 'warning'} variant="ghost" className="text-[9px] px-1">
              {statement.status}
            </FinancialBadge>
          </div>
        </Stack>
      </InspectorSection>

      <InspectorSection title="Explanation" icon="evidence">
        <p className="fin-body-small text-[var(--text-secondary)]">
          Statement from {statement.bank} covering {statement.period_from} to {statement.period_to}. {statement.reconciled_count} of {statement.transaction_count} transactions reconciled.
        </p>
      </InspectorSection>
    </>
  );
}

// ===== Event Context =====
function EventContext({ entity }: { entity: SelectionEntity }) {
  return (
    <InspectorSection title="Event" icon="evidence">
      <p className="fin-body-small text-[var(--text-secondary)]">
        Entity: {entity.id}. Context details not yet available for this event type.
      </p>
    </InspectorSection>
  );
}

// ===== Context Selector =====
function selectContextComponent(entity: SelectionEntity): React.ReactNode {
  switch (entity.type) {
    case 'account':
      return <AccountContext entity={entity} />;
    case 'transaction':
      return <TransactionContext entity={entity} />;
    case 'loan':
      return <LoanContext entity={entity} />;
    case 'card':
      return <CardContext entity={entity} />;
    case 'investment':
      return <InvestmentContext entity={entity} />;
    case 'reconciliation':
      return <ReconciliationContext entity={entity} />;
    default:
      return <EventContext entity={entity as SelectionEntity & { type: string }} />;
  }
}

// ===== Entity Header =====
function EntityHeader({ entity }: { entity: SelectionEntity }) {
  const typeLabels: Record<string, string> = {
    transaction: 'Transaction',
    loan: 'Loan',
    card: 'Credit Card',
    investment: 'Investment',
    account: 'Account',
    reconciliation: 'Reconciliation',
    event: 'Event',
  };

  const iconNames: Record<string, string> = {
    transaction: 'receipt',
    loan: 'loan',
    card: 'credit-card',
    investment: 'investment',
    account: 'wallet',
    reconciliation: 'check-square',
    event: 'evidence',
  };

  const typeLabel = typeLabels[entity.type] ?? entity.type;
  const iconName = iconNames[entity.type] ?? 'evidence';

  return (
    <div className="flex items-center gap-2 px-2 py-1.5 border-b border-[var(--border-subtle)]">
      <FinancialIcon name={iconName} size={12} className="text-[var(--color-selection)] shrink-0" />
      <div className="min-w-0 flex-1">
        <span className="fin-caption font-semibold text-[var(--text-primary)]">{typeLabel}</span>
        <span className="fin-caption text-[var(--text-tertiary)] ml-1">· {entity.id}</span>
      </div>
    </div>
  );
}

// ===== Main Context Panel =====
interface ContextPanelProps {
  className?: string;
}

export function ContextPanel({ className }: ContextPanelProps) {
  const { active } = selectionRuntime.state;
  const insights = passiveInsightRuntime.getInsights();
  const investigative = investigativeInsightRuntime.getInsights();

  // Filter relevant insights for selected entity
  const entityInsights = useMemo(() => {
    if (!active) return [];
    return insights.filter(i =>
      i.relatedEntityId === active.id || i.relatedEntityType === active.type,
    );
  }, [active, insights]);

  const entityInvestigative = useMemo(() => {
    if (!active) return [];
    return investigative.filter(i =>
      i.relatedEntities.some(e => e.entityId === active.id),
    );
  }, [active, investigative]);

  if (!active) {
    return (
      <ScrollRegion className={cn('flex-1 overflow-y-auto', className)}>
        <EmptyContextState
          insights={insights}
          onDismiss={(id) => passiveInsightRuntime.dismiss(id)}
        />
      </ScrollRegion>
    );
  }

  return (
    <ScrollRegion className={cn('flex-1 overflow-y-auto', className)}>
      {/* Entity Header */}
      <EntityHeader entity={active} />

      {/* Entity Context */}
      {selectContextComponent(active)}

      {/* Graph Relationships (Stage 7) */}
      <InspectorSection title="Relationships" icon="graph">
        <GraphContextPanel entityId={String(active.id)} />
      </InspectorSection>

      {/* Insights for Selected Entity */}
      {entityInsights.length > 0 && (
        <InspectorSection title="Insights" icon="behaviour">
          <Stack gap={1}>
            {entityInsights.slice(0, 3).map(insight => (
              <div
                key={insight.id}
                className={cn(
                  'flex items-start gap-1.5 px-1.5 py-1 rounded-[var(--radius-sm)]',
                  severityBg[insight.severity] ?? 'bg-[var(--surface-raised)]',
                )}
              >
                <span className={cn('fin-caption', severityColors[insight.severity] ?? 'text-[var(--text-tertiary)]')}>
                  ·
                </span>
                <span className="fin-caption text-[var(--text-primary)] flex-1">{insight.title}</span>
              </div>
            ))}
          </Stack>
        </InspectorSection>
      )}

      {/* Forecast Summary */}
      <InspectorSection title="Explanation" icon="evidence">
        <p className="fin-body-small text-[var(--text-secondary)]">
          {active.type === 'transaction'
            ? 'Based on recurring patterns, similar transactions avg ₹2,450/month.'
            : active.type === 'loan'
            ? 'Projected completion in 13 years at current payment rate.'
            : 'Predictive analysis not available for this entity type.'}
        </p>
      </InspectorSection>

      {/* Actions */}
      <InspectorSection title="Actions" icon="automate">
        <Stack gap={1}>
          <button className="flex items-center gap-1.5 w-full text-left px-1.5 py-1 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] transition-colors">
            <FinancialIcon name="evidence" size={10} className="text-[var(--text-tertiary)]" />
            <span className="fin-caption text-[var(--text-primary)]">View full evidence trail</span>
          </button>
          <button className="flex items-center gap-1.5 w-full text-left px-1.5 py-1 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] transition-colors">
            <FinancialIcon name="simulate" size={10} className="text-[var(--text-tertiary)]" />
            <span className="fin-caption text-[var(--text-primary)]">Run what-if analysis</span>
          </button>
          <button className="flex items-center gap-1.5 w-full text-left px-1.5 py-1 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] transition-colors">
            <FinancialIcon name="trending-up" size={10} className="text-[var(--text-tertiary)]" />
            <span className="fin-caption text-[var(--text-primary)]">Compare with similar entities</span>
          </button>
        </Stack>
      </InspectorSection>

      {/* Related Investigations */}
      {entityInvestigative.length > 0 && (
        <InspectorSection title="Investigation" icon="brain">
          <Stack gap={1}>
            {entityInvestigative.slice(0, 2).map(insight => (
              <div key={insight.id} className="px-1.5 py-1">
                <p className="fin-caption font-medium text-[var(--text-primary)]">{insight.title}</p>
                <p className="fin-caption text-[var(--text-tertiary)] mt-0.5">{insight.summary.slice(0, 60)}...</p>
              </div>
            ))}
          </Stack>
        </InspectorSection>
      )}
    </ScrollRegion>
  );
}

// ===== Hooks =====
export function useContextPanel() {
  const { active } = selectionRuntime.state;
  return {
    hasSelection: active !== null,
    entityType: active?.type ?? null,
    entityId: active?.id ?? null,
  };
}
