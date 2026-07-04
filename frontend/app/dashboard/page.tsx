'use client';

import { useMemo, useState } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  User,
  Users,
  Wallet,
  TrendingUp,
  Landmark,
  CreditCard,
  Info,
} from 'lucide-react';
import { PageShell } from '@/components/layout/page-shell';
import { KpiCard } from '@/components/ui/kpi-card';
import { SectionCard } from '@/components/ui/section-card';
import {
  useOverviewQuery,
  useMonthlyCashflowQuery,
} from '@/lib/hooks/use-query-finance';
import {
  useCards,
  useLoans,
  useNetWorth,
} from '@/lib/hooks/use-finance-data';
import {
  formatINR,
  formatINRCompact,
  formatPercent,
} from '@/lib/format';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const CHART_COLORS = {
  income: 'hsl(217, 91%, 60%)',
  expense: 'hsl(25, 95%, 53%)',
  trueNet: 'hsl(142, 71%, 45%)',
  trueNetNeg: 'hsl(0, 84%, 60%)',
  recycling: 'hsl(45, 93%, 47%)',
  debt: 'hsl(0, 84%, 60%)',
  neutral: 'hsl(220, 9%, 46%)',
};

// ============================================================
// Mode Toggle
// ============================================================

function ModeToggle({
  mode,
  onModeChange,
}: {
  mode: 'personal' | 'family';
  onModeChange: (mode: 'personal' | 'family') => void;
}) {
  return (
    <Tabs value={mode} onValueChange={(v) => onModeChange(v as 'personal' | 'family')}>
      <TabsList className="h-8" aria-label="Dashboard mode selection">
        <TabsTrigger value="personal" className="text-xs px-3" aria-label="Personal">
          <User className="h-3 w-3 mr-1" aria-hidden="true" />
          Personal
        </TabsTrigger>
        <TabsTrigger value="family" className="text-xs px-3" aria-label="Family">
          <Users className="h-3 w-3 mr-1" aria-hidden="true" />
          Family
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}

// ============================================================
// Dashboard Page
// ============================================================

export default function DashboardPage() {
  const [mode, setMode] = useState<'personal' | 'family'>('personal');
  const { loading: overviewLoading } = useOverviewQuery();
  const { data: netWorth, loading: netWorthLoading } = useNetWorth();
  const { cards, loading: cardsLoading } = useCards();
  const { loans, loading: loansLoading } = useLoans();
  const { data: monthlyCashflow, loading: cashflowLoading } = useMonthlyCashflowQuery();

  const currentMonth = new Date().toISOString().slice(0, 7);

  // Compute debt totals
  const totalCardOutstanding = useMemo(
    () => (cards ?? []).reduce((sum: number, c: any) => sum + (c.outstanding_paise ?? 0), 0),
    [cards]
  );
  const totalLoanOutstanding = useMemo(
    () => (loans ?? []).reduce((sum: number, l: any) => sum + (l.outstanding_paise ?? 0), 0),
    [loans]
  );
  const totalDebt = totalCardOutstanding + totalLoanOutstanding;

  // Net worth color
  const netWorthPaise = netWorth?.net_worth_paise ?? 0;
  const isNetWorthPositive = netWorthPaise >= 0;

  // Executive summary text
  const latestMonthly = (monthlyCashflow?.months?.[0] ?? {}) as Record<string, number | undefined>;
  const trueNetIncomePaise = latestMonthly.net_cashflow_paise ?? 0;
  const trueNetIncomePositive = trueNetIncomePaise >= 0;
  const executiveSummary = useMemo(() => {
    const income = formatINR(trueNetIncomePaise);
    return `${currentMonth} — Your true net income is ${income}.`;
  }, [latestMonthly, currentMonth]);

  const [chartType, setChartType] = useState<'cashflow' | 'networth'>('cashflow');

  const chartData = useMemo(() => {
    if (chartType === 'cashflow') {
      return (monthlyCashflow?.months ?? []).map((m: any) => ({
        label: m.month,
        income: m.real_income_paise ?? 0,
        expense: m.real_expense_paise ?? 0,
        net: (m.real_income_paise ?? 0) - (m.real_expense_paise ?? 0),
      }));
    }
    return []; // networth chart would need separate hook
  }, [chartType, monthlyCashflow]);

  // Upcoming obligations
  const upcoming = useMemo(() => {
    const items: { date: Date; amountPaise: number; label: string; type: 'emi' | 'bill' }[] = [];
    const today = new Date();
    const thirtyDays = new Date(today);
    thirtyDays.setDate(thirtyDays.getDate() + 30);

    // Loans EMI
    (loans ?? []).forEach((loan: any) => {
      if (loan.status !== 'active') return;
      const emiDate = new Date(loan.next_emi_date ?? loan.start_date);
      if (emiDate >= today && emiDate <= thirtyDays) {
        items.push({
          date: emiDate,
          amountPaise: loan.emi_paise ?? 0,
          label: `${loan.name} EMI`,
          type: 'emi',
        });
      }
    });

    // Cards billing date approximation (use statement date as proxy for due)
    (cards ?? []).forEach((card: any) => {
      if (!card.is_active) return;
      const day = card.billing_date ?? card.statement_date ?? 1;
      const due = new Date(today.getFullYear(), today.getMonth(), day);
      if (due < today) due.setMonth(due.getMonth() + 1);
      if (due >= today && due <= thirtyDays) {
        items.push({
          date: due,
          amountPaise: card.minimum_due_paise ?? 0,
          label: `${card.card_name} due`,
          type: 'bill',
        });
      }
    });

    return items.sort((a, b) => a.date.getTime() - b.date.getTime());
  }, [loans, cards]);

  // Health indicators
  const monthlyIncomePaise = latestMonthly.total_income_paise ?? 0;
  const debtToIncome = monthlyIncomePaise > 0 ? (totalDebt / monthlyIncomePaise) * 100 : 0;
  const ccLimitTotal = (cards ?? []).reduce((sum: number, c: any) => sum + (c.credit_limit_paise ?? 0), 0);
  const creditUtilization = ccLimitTotal > 0 ? (totalCardOutstanding / ccLimitTotal) * 100 : 0;
  const recyclingFreq = 0;
  const interestPaise = 0;
  const interestBurden = monthlyIncomePaise > 0 ? (interestPaise / monthlyIncomePaise) * 100 : 0;

  const healthMetrics = [
    {
      label: 'Debt-to-Income',
      value: formatPercent(debtToIncome),
      status: debtToIncome > 500 ? 'bad' : debtToIncome > 300 ? 'warn' : 'good',
      hint: '<300% good, >500% bad',
    },
    {
      label: 'Credit Utilization',
      value: formatPercent(creditUtilization),
      status: creditUtilization > 80 ? 'bad' : creditUtilization > 30 ? 'warn' : 'good',
      hint: '<30% good, >80% bad',
    },
    {
      label: 'Recycling Frequency',
      value: `${recyclingFreq} this month`,
      status: recyclingFreq > 3 ? 'bad' : recyclingFreq > 1 ? 'warn' : 'good',
      hint: '0 good, >3 bad',
    },
    {
      label: 'Interest Burden',
      value: formatPercent(interestBurden),
      status: interestBurden > 15 ? 'bad' : interestBurden > 5 ? 'warn' : 'good',
      hint: '<5% good, >15% bad',
    },
  ];

  const statusDot = (status: string) => {
    if (status === 'good') return 'bg-emerald-500';
    if (status === 'warn') return 'bg-amber-500';
    return 'bg-red-500';
  };

  const isLoading = overviewLoading || cashflowLoading || netWorthLoading || cardsLoading || loansLoading;

  if (isLoading) {
    return (
      <PageShell title="Dashboard" subtitle={`${currentMonth} — Financial health snapshot`} actions={<ModeToggle mode={mode} onModeChange={setMode} />}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-[320px] w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Dashboard"
      subtitle={`${currentMonth} — Financial health snapshot`}
      actions={<ModeToggle mode={mode} onModeChange={setMode} />}
    >
      {/* Row 1 — Executive Summary Bar */}
      <div
        className={`rounded-lg border p-4 ${
          trueNetIncomePositive
            ? 'border-emerald-200 bg-emerald-50/60 dark:border-emerald-900 dark:bg-emerald-950/30'
            : 'border-amber-200 bg-amber-50/60 dark:border-amber-900 dark:bg-amber-950/30'
        }`}
      >
        <div className="flex items-start gap-3">
          <Info className="h-4 w-4 mt-0.5 text-muted-foreground" />
          <p className="text-sm leading-relaxed">{executiveSummary}</p>
        </div>
      </div>

      {/* Row 2 — 4 KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="True Net Income"
          value={formatINR(trueNetIncomePaise)}
          subtext="This month"
          variant={trueNetIncomePositive ? 'success' : 'danger'}
          icon={<Wallet className="h-5 w-5" />}
        />
        <KpiCard
          title="Net Worth"
          value={formatINR(netWorthPaise)}
          subtext="Today"
          variant={isNetWorthPositive ? 'success' : 'danger'}
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <KpiCard
          title="Total Debt"
          value={formatINR(totalDebt)}
          subtext="Cards + Loans"
          variant="danger"
          icon={<Landmark className="h-5 w-5" />}
        />
        <KpiCard
          title="Recycling Cost"
          value={formatINR(0)}
          subtext="This month"
          icon={<CreditCard className="h-5 w-5" />}
        />
      </div>

      {/* Row 3 — Trend Chart */}
      <SectionCard
        title="Cashflow Trend"
        subtitle="Last 6 months"
        action={
          <Tabs value={chartType} onValueChange={(v) => setChartType(v as 'cashflow' | 'networth')}>
            <TabsList className="h-8">
              <TabsTrigger value="cashflow" className="text-xs">Cashflow</TabsTrigger>
              <TabsTrigger value="networth" className="text-xs">Net Worth</TabsTrigger>
            </TabsList>
          </Tabs>
        }
      >
        <div className="h-[280px] w-full">
          {chartData.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">No data</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v: number) => formatINRCompact(v)} tick={{ fontSize: 11 }} width={60} />
                <Tooltip
                  formatter={(value: number) => formatINR(value)}
                  labelFormatter={(label) => label}
                />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="income" name="Real Income" fill={CHART_COLORS.income} radius={[3, 3, 0, 0]} />
                <Bar dataKey="expense" name="Real Expense" fill={CHART_COLORS.expense} radius={[3, 3, 0, 0]} />
                <Line
                  type="monotone"
                  dataKey="net"
                  name="True Net"
                  stroke={(chartData[chartData.length - 1]?.net ?? 0) >= 0 ? CHART_COLORS.trueNet : CHART_COLORS.trueNetNeg}
                  strokeWidth={2}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </div>
      </SectionCard>

      {/* Row 4 — 3 Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Debt Breakdown */}
        <SectionCard title="Debt Breakdown" subtitle="Outstanding by liability">
          <div className="space-y-3">
            {(cards ?? []).filter((c: any) => c.is_active).length === 0 &&
            (loans ?? []).filter((l: any) => l.status === 'active').length === 0 ? (
              <p className="text-sm text-muted-foreground">No active debt.</p>
            ) : (
              <>
                {(cards ?? [])
                  .filter((c: any) => c.is_active)
                  .map((card: any) => (
                    <div key={card.id} className="flex items-center justify-between text-sm">
                      <span className="truncate mr-2">{card.card_name}</span>
                      <span className="font-medium">{formatINR(card.outstanding_paise)}</span>
                    </div>
                  ))}
                {(loans ?? [])
                  .filter((l: any) => l.status === 'active')
                  .map((loan: any) => (
                    <div key={loan.id} className="flex items-center justify-between text-sm">
                      <span className="truncate mr-2">{loan.name}</span>
                      <span className="font-medium">{formatINR(loan.outstanding_paise)}</span>
                    </div>
                  ))}
                <div className="flex items-center justify-between border-t pt-2 text-sm font-semibold">
                  <span>Total</span>
                  <span>{formatINR(totalDebt)}</span>
                </div>
              </>
            )}
          </div>
        </SectionCard>

        {/* Upcoming Obligations */}
        <SectionCard title="Upcoming Obligations" subtitle="Next 30 days">
          <div className="space-y-2">
            {upcoming.length === 0 ? (
              <p className="text-sm text-muted-foreground">No upcoming dues.</p>
            ) : (
              upcoming.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between gap-2 text-sm border-b last:border-0 pb-2 last:pb-0"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate">{item.label}</p>
                    <p className="text-xs text-muted-foreground">
                      {item.date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                    </p>
                  </div>
                  <span className="text-sm font-medium">{formatINR(item.amountPaise)}</span>
                </div>
              ))
            )}
          </div>
        </SectionCard>
      </div>

      {/* Row 5 — Health Indicators */}
      <SectionCard title="Financial Health Indicators" subtitle="Key ratios for this month">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {healthMetrics.map((m) => (
            <div key={m.label} className="flex items-center justify-between rounded-lg border bg-muted/40 px-3 py-2">
              <div>
                <p className="text-xs text-muted-foreground">{m.label}</p>
                <p className="text-sm font-semibold">{m.value}</p>
              </div>
              <span className={`h-2.5 w-2.5 rounded-full ${statusDot(m.status)}`} title={m.hint} />
            </div>
          ))}
        </div>
      </SectionCard>
    </PageShell>
  );
}