'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

import { Badge } from '@/components/ui/badge';
import { PageShell } from '@/components/layout/page-shell';
import { KpiCard } from '@/components/ui/kpi-card';
import { SectionCard } from '@/components/ui/section-card';
import { useInvestments, useCreateInvestment } from '@/lib/hooks/use-finance-data';
import { formatINR, formatPercent, paiseToRupees, rupeesToPaise } from '@/lib/format';
import { Plus, TrendingUp, Wallet } from 'lucide-react';

const INVESTMENT_TYPES = [
  { value: 'mutual_fund', label: 'Mutual Fund' },
  { value: 'stock', label: 'Stock' },
  { value: 'fd', label: 'Fixed Deposit' },
  { value: 'gold', label: 'Gold' },
  { value: 'bond', label: 'Bond' },
  { value: 'other', label: 'Other' },
] as const;

// ============================================================
// Types
// ============================================================

interface InvestmentFormData {
  name: string;
  investment_type: typeof INVESTMENT_TYPES[number]['value'];
  units: string;
  buy_price_rupees: string;
  buy_date: string;
  current_price_rupees: string;
  amc_broker: string;
  folio_number: string;
  notes: string;
}

// ============================================================
// Investment Form
// ============================================================

function InvestmentForm({ initialData, onSubmit, onCancel }: { initialData?: any; onSubmit: (data: InvestmentFormData) => void; onCancel: () => void }) {
  const [formData, setFormData] = useState<InvestmentFormData>({
    name: initialData?.name || '',
    investment_type: initialData?.investment_type || 'mutual_fund',
    units: initialData?.units ? String(initialData.units) : '',
    buy_price_rupees: initialData?.buy_price_paise ? String(paiseToRupees(initialData.buy_price_paise)) : '',
    buy_date: initialData?.buy_date ? initialData.buy_date.split('T')[0] : '',
    current_price_rupees: initialData?.current_price_paise ? String(paiseToRupees(initialData.current_price_paise)) : '',
    amc_broker: initialData?.amc_broker || '',
    folio_number: initialData?.folio_number || '',
    notes: initialData?.notes || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div><Label htmlFor="name">Investment Name *</Label><Input id="name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required /></div>
        <div><Label htmlFor="investment_type">Type *</Label><Select value={formData.investment_type} onValueChange={(v) => setFormData({ ...formData, investment_type: v as any })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{INVESTMENT_TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent></Select></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div><Label htmlFor="units">Units / Quantity *</Label><Input id="units" type="number" value={formData.units} onChange={(e) => setFormData({ ...formData, units: e.target.value })} required /></div>
        <div><Label htmlFor="buy_price_rupees">Buy Price per Unit (₹) *</Label><Input id="buy_price_rupees" type="number" step="0.01" value={formData.buy_price_rupees} onChange={(e) => setFormData({ ...formData, buy_price_rupees: e.target.value })} required /></div>
        <div><Label htmlFor="current_price_rupees">Current Price per Unit (₹)</Label><Input id="current_price_rupees" type="number" step="0.01" value={formData.current_price_rupees} onChange={(e) => setFormData({ ...formData, current_price_rupees: e.target.value })} /></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div><Label htmlFor="buy_date">Buy Date *</Label><Input id="buy_date" type="date" value={formData.buy_date} onChange={(e) => setFormData({ ...formData, buy_date: e.target.value })} required /></div>
        <div><Label htmlFor="amc_broker">AMC / Broker</Label><Input id="amc_broker" value={formData.amc_broker} onChange={(e) => setFormData({ ...formData, amc_broker: e.target.value })} /></div>
      </div>
      <div><Label htmlFor="folio_number">Folio Number (optional)</Label><Input id="folio_number" value={formData.folio_number} onChange={(e) => setFormData({ ...formData, folio_number: e.target.value })} /></div>
      <div><Label htmlFor="notes">Notes</Label><Input id="notes" value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} /></div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
        <Button type="submit">{initialData ? 'Update' : 'Add Investment'}</Button>
      </div>
    </form>
  );
}

// ============================================================
// Main
// ============================================================

export default function InvestmentsPage() {
  const { investments, refetch } = useInvestments();
  const { createInvestment } = useCreateInvestment();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);

  const investmentsList = investments ?? [];

  const totalInvested = investmentsList.reduce((s: number, i: any) => s + ((i.units || 0) * (i.buy_price_paise || 0)), 0);
  const currentValue = investmentsList.reduce((s: number, i: any) => s + ((i.units || 0) * (i.current_price_paise || i.buy_price_paise || 0)), 0);
  const gainLoss = currentValue - totalInvested;
  const gainPercent = totalInvested > 0 ? (gainLoss / totalInvested) * 100 : 0;

  const handleSubmit = async (form: InvestmentFormData) => {
    const payload: any = {
      name: form.name,
      investment_type: form.investment_type,
      units: parseFloat(form.units) || 0,
      buy_price_paise: rupeesToPaise(parseFloat(form.buy_price_rupees) || 0),
      current_price_paise: form.current_price_rupees ? rupeesToPaise(parseFloat(form.current_price_rupees) || 0) : undefined,
      buy_date: form.buy_date,
      amc_broker: form.amc_broker || undefined,
      folio_number: form.folio_number || undefined,
      notes: form.notes || undefined,
    };
    if (editing) {
      await createInvestment(payload); // backend uses POST for now; edit can be added later
    } else {
      await createInvestment(payload);
    }
    refetch();
    setDialogOpen(false);
    setEditing(null);
  };

  const openEdit = (inv: any) => {
    setEditing(inv);
    setDialogOpen(true);
  };

  return (
    <PageShell
      title="Investments"
      subtitle={`${investmentsList.length} holdings`}
      actions={
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-2" />Add Investment</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>{editing ? 'Edit Investment' : 'Add Investment'}</DialogTitle></DialogHeader>
            <InvestmentForm initialData={editing} onSubmit={handleSubmit} onCancel={() => { setEditing(null); setDialogOpen(false); }} />
          </DialogContent>
        </Dialog>
      }
    >
      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="Total Invested" value={formatINR(totalInvested)} subtext="Cost basis" icon={<Wallet className="h-5 w-5" />} />
        <KpiCard title="Current Value" value={formatINR(currentValue)} subtext="Mark to market" icon={<TrendingUp className="h-5 w-5" />} />
        <KpiCard title="Total Gain/Loss" value={formatINR(gainLoss)} subtext={formatPercent(gainPercent)} variant={gainLoss >= 0 ? 'success' : 'danger'} />
      </div>

      {/* Table */}
      <SectionCard title="Holdings">
        {investmentsList.length === 0 ? (
          <p className="text-sm text-muted-foreground">No investments yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-muted/40"><th className="text-left px-4 py-2">Name</th><th className="text-left px-4 py-2">Type</th><th className="text-right px-4 py-2">Units</th><th className="text-right px-4 py-2">Buy</th><th className="text-right px-4 py-2">Current</th><th className="text-right px-4 py-2">Value</th><th className="text-right px-4 py-2">Gain</th></tr></thead>
              <tbody>
                {investmentsList.map((inv: any) => {
                  const buy = inv.buy_price_paise || 0;
                  const curr = inv.current_price_paise || buy;
                  const units = inv.units || 0;
                  const val = units * curr;
                  const cost = units * buy;
                  const gl = val - cost;
                  const pct = cost > 0 ? (gl / cost) * 100 : 0;
                  return (
                    <tr key={inv.id} className="border-b last:border-0 hover:bg-muted/40">
                      <td className="px-4 py-2">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{inv.name}</span>
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(inv)}><Plus className="h-3.5 w-3.5 rotate-45" /></Button>
                        </div>
                        <p className="text-xs text-muted-foreground">{inv.amc_broker || ''} {inv.folio_number ? `• ${inv.folio_number}` : ''}</p>
                      </td>
                      <td className="px-4 py-2"><Badge variant="secondary">{inv.investment_type}</Badge></td>
                      <td className="px-4 py-2 text-right">{units}</td>
                      <td className="px-4 py-2 text-right">{formatINR(buy)}</td>
                      <td className="px-4 py-2 text-right">{formatINR(curr)}</td>
                      <td className="px-4 py-2 text-right font-medium">{formatINR(val)}</td>
                      <td className={`px-4 py-2 text-right font-medium ${gl >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{formatPercent(pct)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </PageShell>
  );
}