'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PageShell } from '@/components/layout/page-shell';
import { KpiCard } from '@/components/ui/kpi-card';
import { SectionCard } from '@/components/ui/section-card';
import {
  useLoans,
  useCreateLoan,
  useDeleteLoan,
  useAmortizationSchedule,
  useSimulatePrepayment,
} from '@/lib/hooks/use-finance-data';
import { fetchLoanPayoffProjection } from '@/lib/api/client';
import { formatINR, formatMonths, formatDate } from '@/lib/format';
import { Plus, Landmark, Trash2, Table2, TrendingDown, Clock, Download } from 'lucide-react';
import type { Loan, LoanCreate, AmortizationSchedule, PrepaymentResult } from '@/types/loan';
import type { LoanPayoffProjection } from '@/types/financial';

const LOAN_TYPE_LABELS: Record<string, string> = {
  home: 'Home Loan',
  car: 'Car Loan',
  personal: 'Personal Loan',
  education: 'Education Loan',
  credit_card: 'Credit Card',
  gold: 'Gold Loan',
  other: 'Other',
};

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
  defaulted: 'bg-red-100 text-red-800',
};

export default function LoansPage() {
  const { loans } = useLoans();
  const { createLoan } = useCreateLoan();
  const { deleteLoan, deleting } = useDeleteLoan();
  const { simulatePrepayment, simulating: simulatingPrepayment } = useSimulatePrepayment();

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [selectedLoanId, setSelectedLoanId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [prepaymentResult, setPrepaymentResult] = useState<PrepaymentResult | null>(null);
  const [payoffProjection, setPayoffProjection] = useState<LoanPayoffProjection | null>(null);
  const [loadingPayoff, setLoadingPayoff] = useState(false);
  const [toolsError, setToolsError] = useState<string | null>(null);

  const { data: amortizationData, loading: amortizationLoading } = useAmortizationSchedule();
  const selectedLoan = (loans ?? []).find((l) => l.id === selectedLoanId);

  const totalOutstanding = (loans ?? [])
    .filter((l) => l.status === 'active')
    .reduce((s, l) => s + (l.outstanding_paise || 0), 0);

  const totalEmi = (loans ?? [])
    .filter((l) => l.status === 'active')
    .reduce((s, l) => s + (l.emi_paise || 0), 0);

  const activeTenures = (loans ?? [])
    .filter((l) => l.status === 'active')
    .map((l) => l.tenure_months || 0);

  // Use loans array directly (it's already extracted from the response)
  const loansArray = loans ?? [];

  const maxTenure = activeTenures.length > 0 ? Math.max(...activeTenures) : 0;

  const handleCreate = (formData: LoanCreate) => {
    createLoan(formData);
    setAddDialogOpen(false);
  };

  const handleDelete = (loan: Loan) => {
    if (!confirm(`Delete "${loan.name}"?`)) return;
    deleteLoan(loan.id);
  };

  const handleSimulatePrepayment = (
    amount: number,
    date: string,
    strategy: 'REDUCE_TENURE' | 'REDUCE_EMI'
  ) => {
    if (!selectedLoanId) return;
    setToolsError(null);
    simulatePrepayment({
      loanId: selectedLoanId,
      data: {
        extra_payment_paise: Math.round(amount * 100),
        extra_payment_date: date,
        strategy,
      },
    });
  };

  const loadPayoffProjection = async () => {
    if (!selectedLoanId) return;
    setLoadingPayoff(true);
    setToolsError(null);
    try {
      const result = await fetchLoanPayoffProjection(selectedLoanId);
      setPayoffProjection(result);
    } catch (err) {
      setToolsError(
        err instanceof Error ? err.message : 'Failed to load payoff projection'
      );
    } finally {
      setLoadingPayoff(false);
    }
  };

  const openDetail = (loanId: number) => {
    setSelectedLoanId(loanId);
    setPrepaymentResult(null);
    setPayoffProjection(null);
    setToolsError(null);
    setActiveTab('overview');
  };

  return (
    <PageShell
      title="Loans"
      subtitle={`${loansArray.filter((l) => l.status === 'active').length} active`}
      actions={
        <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Loan
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Loan</DialogTitle>
            </DialogHeader>
            <LoanForm
              onSubmit={handleCreate}
              onCancel={() => setAddDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      }
    >
      {/* Summary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Total Outstanding"
          value={formatINR(totalOutstanding)}
          subtext="Active loans"
          variant="danger"
          icon={<Landmark className="h-5 w-5" />}
        />
        <KpiCard
          title="Monthly EMI"
          value={formatINR(totalEmi)}
          subtext="Total outflow"
          icon={<Clock className="h-5 w-5" />}
        />
        <KpiCard
          title="Longest Tenure"
          value={formatMonths(maxTenure)}
          subtext="Remaining"
          icon={<TrendingDown className="h-5 w-5" />}
        />
      </div>

      {/* Loan List */}
      {loansArray.length === 0 ? (
        <Card className="p-8 text-center">
          <Landmark className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-medium mb-2">No Loans Yet</h3>
          <p className="text-muted-foreground mb-4">
            Add your first loan to track amortization and payoff.
          </p>
          <Button onClick={() => setAddDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Loan
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loansArray.map((loan) => {
            const progress =
              loan.principal_paise && loan.principal_paise > 0
                ? ((loan.principal_paise - loan.outstanding_paise) /
                    loan.principal_paise) *
                  100
                : 0;
            return (
              <Card
                key={loan.id}
                className={`p-4 ${
                  selectedLoanId === loan.id ? 'ring-2 ring-primary' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-semibold">{loan.name}</h3>
                    <p className="text-xs text-muted-foreground">
                      {loan.lender || '—'}
                    </p>
                  </div>
                  <Badge
                    className={
                      STATUS_COLORS[loan.status] || STATUS_COLORS.active
                    }
                  >
                    {loan.status.toUpperCase()}
                  </Badge>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Outstanding</span>
                    <span className="font-medium">
                      {formatINR(loan.outstanding_paise)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">EMI</span>
                    <span className="font-medium">
                      {formatINR(loan.emi_paise)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Rate</span>
                    <span className="font-medium">
                      {loan.interest_rate != null
                        ? `${loan.interest_rate.toFixed(2)}% p.a.`
                        : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Tenure</span>
                    <span className="font-medium">
                      {formatMonths(loan.tenure_months)}
                    </span>
                  </div>
                  {loan.next_emi_date && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Next EMI</span>
                      <span className="font-medium">
                        {formatDate(loan.next_emi_date)}
                      </span>
                    </div>
                  )}
                </div>
                <div className="mt-3">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Paid</span>
                    <span className="font-medium">{progress.toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary"
                      style={{ width: `${Math.min(progress, 100)}%` }}
                    />
                  </div>
                </div>
                <div className="mt-3 flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => openDetail(loan.id)}
                  >
                    <Table2 className="h-3.5 w-3.5 mr-1.5" />
                    Details
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(loan)}
                    disabled={deleting}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Detail Panel */}
      {selectedLoan && (
        <SectionCard
          title={selectedLoan.name}
          subtitle={`${
            LOAN_TYPE_LABELS[selectedLoan.loan_type] || selectedLoan.loan_type
          } • ${selectedLoan.lender || 'Unknown lender'}`}
        >
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="schedule">Amortization Schedule</TabsTrigger>
              <TabsTrigger value="tools">Tools</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-lg border bg-muted/40 p-3">
                  <p className="text-xs text-muted-foreground">Principal</p>
                  <p className="text-lg font-semibold">
                    {formatINR(selectedLoan.principal_paise)}
                  </p>
                </div>
                <div className="rounded-lg border bg-muted/40 p-3">
                  <p className="text-xs text-muted-foreground">Outstanding</p>
                  <p className="text-lg font-semibold">
                    {formatINR(selectedLoan.outstanding_paise)}
                  </p>
                </div>
                <div className="rounded-lg border bg-muted/40 p-3">
                  <p className="text-xs text-muted-foreground">EMI</p>
                  <p className="text-lg font-semibold">
                    {formatINR(selectedLoan.emi_paise)}
                  </p>
                </div>
              </div>
              {selectedLoan.notes && (
                <p className="text-sm text-muted-foreground">
                  {selectedLoan.notes}
                </p>
              )}
            </TabsContent>

            <TabsContent value="schedule">
              {amortizationLoading ? (
                <p className="text-sm text-muted-foreground">
                  Loading amortization…
                </p>
              ) : amortizationData ? (
                <AmortizationView data={amortizationData} />
              ) : (
                <p className="text-sm text-muted-foreground">
                  No amortization data available.
                </p>
              )}
            </TabsContent>

            <TabsContent value="tools" className="space-y-4">
              {toolsError && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {toolsError}
                </div>
              )}
              <PrepaymentSimulator
                onSimulate={handleSimulatePrepayment}
                result={prepaymentResult}
                loading={simulatingPrepayment}
              />
              <PayoffProjection
                projection={payoffProjection}
                loading={loadingPayoff}
                onLoad={loadPayoffProjection}
              />
            </TabsContent>
          </Tabs>
        </SectionCard>
      )}
    </PageShell>
  );
}

// ─────────────────────────────────────────────
// LoanForm
// ─────────────────────────────────────────────

function LoanForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (data: LoanCreate) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<Partial<LoanCreate>>({
    loan_type: 'personal',
    status: 'active',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !formData.name ||
      !formData.principal_paise ||
      !formData.outstanding_paise ||
      !formData.interest_rate ||
      !formData.start_date
    )
      return;
    onSubmit(formData as LoanCreate);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">Loan Name *</Label>
          <Input
            id="name"
            value={formData.name || ''}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>
        <div>
          <Label htmlFor="lender">Lender</Label>
          <Input
            id="lender"
            value={formData.lender || ''}
            onChange={(e) =>
              setFormData({ ...formData, lender: e.target.value })
            }
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="loan_type">Loan Type</Label>
          <Select
            value={formData.loan_type}
            onValueChange={(v) =>
              setFormData({
                ...formData,
                loan_type: v as LoanCreate['loan_type'],
              })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(LOAN_TYPE_LABELS).map(([k, v]) => (
                <SelectItem key={k} value={k}>
                  {v}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="status">Status</Label>
          <Select
            value={formData.status}
            onValueChange={(v) =>
              setFormData({
                ...formData,
                status: v as LoanCreate['status'],
              })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
              <SelectItem value="defaulted">Defaulted</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="principal">Principal (₹) *</Label>
          <Input
            id="principal"
            type="number"
            value={
              formData.principal_paise ? formData.principal_paise / 100 : ''
            }
            onChange={(e) =>
              setFormData({
                ...formData,
                principal_paise:
                  Math.round(parseFloat(e.target.value) * 100) || 0,
              })
            }
            required
          />
        </div>
        <div>
          <Label htmlFor="outstanding">Outstanding (₹) *</Label>
          <Input
            id="outstanding"
            type="number"
            value={
              formData.outstanding_paise
                ? formData.outstanding_paise / 100
                : ''
            }
            onChange={(e) =>
              setFormData({
                ...formData,
                outstanding_paise:
                  Math.round(parseFloat(e.target.value) * 100) || 0,
              })
            }
            required
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="interest_rate">Interest Rate (% p.a.) *</Label>
          <Input
            id="interest_rate"
            type="number"
            step="0.01"
            value={formData.interest_rate || ''}
            onChange={(e) =>
              setFormData({
                ...formData,
                interest_rate: parseFloat(e.target.value) || 0,
              })
            }
            required
          />
        </div>
        <div>
          <Label htmlFor="emi">Monthly EMI (₹)</Label>
          <Input
            id="emi"
            type="number"
            value={formData.emi_paise ? formData.emi_paise / 100 : ''}
            onChange={(e) =>
              setFormData({
                ...formData,
                emi_paise: e.target.value
                  ? Math.round(parseFloat(e.target.value) * 100)
                  : undefined,
              })
            }
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="tenure">Tenure (months)</Label>
          <Input
            id="tenure"
            type="number"
            value={formData.tenure_months ?? ''}
            onChange={(e) =>
              setFormData({
                ...formData,
                tenure_months: e.target.value
                  ? parseInt(e.target.value, 10)
                  : undefined,
              })
            }
          />
        </div>
        <div>
          <Label htmlFor="start_date">Start Date *</Label>
          <Input
            id="start_date"
            type="date"
            value={formData.start_date || ''}
            onChange={(e) =>
              setFormData({ ...formData, start_date: e.target.value })
            }
            required
          />
        </div>
      </div>
      <div>
        <Label htmlFor="notes">Notes</Label>
        <Input
          id="notes"
          value={formData.notes || ''}
          onChange={(e) =>
            setFormData({ ...formData, notes: e.target.value })
          }
        />
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">Create Loan</Button>
      </div>
    </form>
  );
}

// ─────────────────────────────────────────────
// AmortizationView
// ─────────────────────────────────────────────

function AmortizationView({ data }: { data: AmortizationSchedule }) {
  const [filter, setFilter] = useState<'all' | 'future' | 'year'>('future');
  const [year, setYear] = useState('');

  const schedule = (() => {
    const today = new Date();
    if (filter === 'future')
      return data.schedule.filter((e) => new Date(e.emi_date) >= today);
    if (filter === 'year' && year)
      return data.schedule.filter(
        (e) => new Date(e.emi_date).getFullYear() === parseInt(year, 10)
      );
    return data.schedule;
  })();

  const years = Array.from(
    new Set(data.schedule.map((e) => new Date(e.emi_date).getFullYear()))
  );

  const handleExport = () => {
    const headers = [
      'Month',
      'EMI Date',
      'EMI',
      'Principal',
      'Interest',
      'Balance',
    ];
    const rows = schedule.map((e) => [
      e.period,
      e.emi_date,
      e.emi_paise,
      e.principal_paise,
      e.interest_paise,
      e.remaining_principal_paise,
    ]);
    const csv = [headers, ...rows]
      .map((r) =>
        r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')
      )
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'amortization.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Select
            value={filter}
            onValueChange={(v) => setFilter(v as 'all' | 'future' | 'year')}
          >
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="future">Future</SelectItem>
              <SelectItem value="year">By Year</SelectItem>
            </SelectContent>
          </Select>
          {filter === 'year' && (
            <Select value={year} onValueChange={setYear}>
              <SelectTrigger className="w-28">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                {years.map((yr) => (
                  <SelectItem key={yr} value={String(yr)}>
                    {yr}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={handleExport}>
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>
      <div className="border rounded-lg overflow-auto max-h-[500px]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-muted/60">
            <tr className="border-b">
              <th className="text-left px-3 py-2">#</th>
              <th className="text-left px-3 py-2">Date</th>
              <th className="text-right px-3 py-2">EMI</th>
              <th className="text-right px-3 py-2">Principal</th>
              <th className="text-right px-3 py-2">Interest</th>
              <th className="text-right px-3 py-2">Balance</th>
            </tr>
          </thead>
          <tbody>
            {schedule.map((entry) => {
              const entryDate = new Date(entry.emi_date);
              const today = new Date();
              const isPast = entryDate < today;
              const isToday =
                entryDate.toDateString() === today.toDateString();
              return (
                <tr
                  key={entry.period}
                  className={`border-b last:border-0 ${
                    isToday
                      ? 'bg-primary/5'
                      : isPast
                      ? 'opacity-60'
                      : ''
                  }`}
                >
                  <td className="px-3 py-2">{entry.period}</td>
                  <td className="px-3 py-2">{formatDate(entry.emi_date)}</td>
                  <td className="px-3 py-2 text-right">
                    {formatINR(entry.emi_paise)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {formatINR(entry.principal_paise)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {formatINR(entry.interest_paise)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {formatINR(entry.remaining_principal_paise)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// PrepaymentSimulator
// ─────────────────────────────────────────────

function PrepaymentSimulator({
  onSimulate,
  result,
  loading,
}: {
  onSimulate: (
    amount: number,
    date: string,
    strategy: 'REDUCE_TENURE' | 'REDUCE_EMI'
  ) => void;
  result: PrepaymentResult | null;
  loading: boolean;
}) {
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0] ?? '');
  const [strategy, setStrategy] = useState<'REDUCE_TENURE' | 'REDUCE_EMI'>(
    'REDUCE_TENURE'
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseFloat(amount);
    if (num > 0 && date) onSimulate(num, date, strategy);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingDown className="h-4 w-4" />
          Prepayment Simulator
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="prepay-amount">Extra Payment (₹)</Label>
              <Input
                id="prepay-amount"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="prepay-date">Payment Date</Label>
              <Input
                id="prepay-date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="strategy">Strategy</Label>
              <Select
                value={strategy}
                onValueChange={(v) =>
                  setStrategy(v as 'REDUCE_TENURE' | 'REDUCE_EMI')
                }
              >
                <SelectTrigger id="strategy">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="REDUCE_TENURE">Reduce Tenure</SelectItem>
                  <SelectItem value="REDUCE_EMI">Reduce EMI</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Simulating…' : 'Run Simulation'}
          </Button>
        </form>
        {result && (
          <div className="space-y-3 pt-4 border-t">
            <h4 className="font-medium text-sm text-muted-foreground">
              Simulation Results
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-emerald-50 dark:bg-emerald-950/30 p-3 rounded-lg">
                <p className="text-xs text-emerald-600">Interest Saved</p>
                <p className="text-lg font-semibold text-emerald-700">
                  {formatINR(result.interest_saved_paise)}
                </p>
              </div>
              <div className="bg-blue-50 dark:bg-blue-950/30 p-3 rounded-lg">
                <p className="text-xs text-blue-600">Months Saved</p>
                <p className="text-lg font-semibold text-blue-700">
                  {result.months_saved}
                </p>
              </div>
              <div className="bg-muted p-3 rounded-lg">
                <p className="text-xs text-muted-foreground">
                  New Closure Date
                </p>
                <p className="text-sm font-medium">
                  {new Date(result.new_closure_date).toLocaleDateString(
                    'en-IN'
                  )}
                </p>
              </div>
              <div className="bg-muted p-3 rounded-lg">
                <p className="text-xs text-muted-foreground">New EMI</p>
                <p className="text-sm font-medium">
                  {formatINR(result.new_emi_paise)}
                </p>
              </div>
            </div>
            <div className="bg-muted p-3 rounded-lg">
              <p className="text-xs text-muted-foreground">
                Effective Annual Return
              </p>
              <p className="text-lg font-semibold">
                {result.effective_annual_return_percent.toFixed(2)}%
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Compare this to your investment returns to decide if prepayment
                makes sense.
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─────────────────────────────────────────────
// PayoffProjection
// ─────────────────────────────────────────────

function PayoffProjection({
  projection,
  loading,
  onLoad,
}: {
  projection: LoanPayoffProjection | null;
  loading: boolean;
  onLoad: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Payoff Projection
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!projection ? (
          <div className="text-center py-4">
            <p className="text-muted-foreground text-sm mb-3">
              See when your loan will be fully paid off based on current
              payments.
            </p>
            <Button onClick={onLoad} disabled={loading}>
              {loading ? 'Loading…' : 'Load Projection'}
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-muted p-3 rounded-lg">
                <p className="text-xs text-muted-foreground">Payoff Date</p>
                <p className="text-lg font-semibold">
                  {projection.payoff_date
                    ? new Date(projection.payoff_date).toLocaleDateString(
                        'en-IN'
                      )
                    : '—'}
                </p>
              </div>
              <div className="bg-muted p-3 rounded-lg">
                <p className="text-xs text-muted-foreground">
                  Months Remaining
                </p>
                <p className="text-lg font-semibold">
                  {projection.remaining_months ?? '—'}
                </p>
              </div>
              <div className="bg-muted p-3 rounded-lg">
                <p className="text-xs text-muted-foreground">
                  Total Interest Remaining
                </p>
                <p className="text-lg font-semibold">
                  {formatINR(projection.total_remaining_interest_paise ?? 0)}
                </p>
              </div>
              <div className="bg-muted p-3 rounded-lg">
                <p className="text-xs text-muted-foreground">
                  Remaining Principal
                </p>
                <p className="text-lg font-semibold">
                  {formatINR(projection.remaining_principal_paise ?? 0)}
                </p>
              </div>
            </div>
            <Button
              onClick={onLoad}
              disabled={loading}
              variant="outline"
              className="w-full"
            >
              {loading ? 'Refreshing…' : 'Refresh Projection'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}