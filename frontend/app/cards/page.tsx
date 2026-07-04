'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { PageShell } from '@/components/layout/page-shell';
import { KpiCard } from '@/components/ui/kpi-card';
import { useCards, useCreateCard, useUpdateCard, useDeleteCard } from '@/lib/hooks/use-finance-data';
import { formatINR, formatDate, formatPercent, formatCardType } from '@/lib/format';
import { Plus, Pencil, Trash2, Eye } from 'lucide-react';
import type { Card as CardType } from '@/lib/api/client';

const CARD_TYPES = [
  { value: 'visa', label: 'Visa' },
  { value: 'mastercard', label: 'Mastercard' },
  { value: 'rupay', label: 'RuPay' },
  { value: 'amex', label: 'American Express' },
  { value: 'diners', label: 'Diners Club' },
] as const;

const CARD_GRADIENTS = [
  { name: 'Midnight', value: 'from-slate-700 to-slate-900' },
  { name: 'Ocean', value: 'from-blue-700 to-indigo-900' },
  { name: 'Amethyst', value: 'from-purple-700 to-indigo-900' },
  { name: 'Ember', value: 'from-red-700 to-orange-900' },
  { name: 'Forest', value: 'from-emerald-700 to-teal-900' },
  { name: 'Gold', value: 'from-amber-600 to-yellow-800' },
];

// ============================================================
// Types
// ============================================================

interface CardFormData {
  card_name: string;
  card_type: typeof CARD_TYPES[number]['value'];
  issuer: string;
  last_four: string;
  cardholder_name: string;
  credit_limit_rupees: string;
  outstanding_rupees: string;
  billing_date: string;
  payment_due_date: string;
  apr: string;
  reward_type: string;
  linked_account_id: string;
  card_gradient: string;
  is_active: boolean;
}

// ============================================================
// Card Visual
// ============================================================

function CardVisual({ card, onEdit, onDelete, onViewTx }: { card: CardType; onEdit: (c: CardType) => void; onDelete: (id: number) => void; onViewTx: (c: CardType) => void }) {
  const utilization = card.credit_limit_paise && card.credit_limit_paise > 0 ? (card.outstanding_paise / card.credit_limit_paise) * 100 : 0;

  return (
    <div className="rounded-xl border bg-card p-4 space-y-3">
      {/* Visual */}
      <div className={`relative w-full aspect-[1.586] rounded-xl overflow-hidden bg-gradient-to-br ${typeof card.card_gradient === 'string' ? card.card_gradient : CARD_GRADIENTS[0]!.value}`}>
        <div className="relative z-10 p-5 flex flex-col justify-between h-full text-white">
          <div className="flex justify-between items-start">
            <span className="text-sm font-semibold">{card.issuer}</span>
            <span className="text-xs font-medium uppercase">{formatCardType(card.card_type)}</span>
          </div>
          <div className="font-mono text-lg tracking-[0.2em] mt-3">•••• •••• •••• {card.last_four}</div>
          <div className="flex justify-between items-end mt-3">
            <div>
              <p className="text-[10px] opacity-70 uppercase tracking-wider">Card Holder</p>
              <p className="text-xs font-medium uppercase">{card.cardholder_name || 'YOUR NAME'}</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] opacity-70 uppercase tracking-wider">Limit</p>
              <p className="text-xs font-medium">{formatINR(card.credit_limit_paise)}</p>
            </div>
          </div>
        </div>
        {/* Utilization bar */}
        <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-black/20">
          <div
            className="h-full"
            style={{
              width: `${Math.min(utilization, 100)}%`,
              backgroundColor: utilization > 70 ? '#ef4444' : utilization > 30 ? '#f59e0b' : '#22c55e'
            }}
          />
        </div>
      </div>

      {/* Meta */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">{card.card_name}</h3>
          <Badge variant="secondary" className="text-[10px]">{formatCardType(card.card_type)}</Badge>
        </div>
        <div className="grid grid-cols-2 gap-1 text-xs">
          <div>
            <span className="text-muted-foreground">Card:</span>
            <span className="ml-1 font-medium">{card.card_name}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Type:</span>
            <span className="ml-1 font-medium">{formatCardType(card.card_type)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Issuer:</span>
            <span className="ml-1 font-medium">{card.issuer}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Limit:</span>
            <span className="ml-1 font-medium">{formatINR(card.credit_limit_paise)}</span>
          </div>
        </div>
        <p className="text-[10px] text-muted-foreground">Updated: {formatDate(card.updated_at)}</p>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <Button variant="outline" size="sm" className="flex-1" onClick={() => onViewTx(card)}>
          <Eye className="h-3.5 w-3.5 mr-1.5" /> Transactions
        </Button>
        <Button variant="ghost" size="icon" onClick={() => onEdit(card)}><Pencil className="h-4 w-4" /></Button>
        <Button variant="ghost" size="icon" onClick={() => onDelete(card.id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
      </div>
    </div>
  );
}

// ============================================================
// Main
// ============================================================

export default function CardsPage() {
  const { cards } = useCards();
  const { createCard } = useCreateCard();
  const { updateCard } = useUpdateCard();
  const { deleteCard } = useDeleteCard();
  
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCard, setEditingCard] = useState<CardType | null>(null);

  const activeCards = (cards ?? []).filter((c) => c.is_active);
  const closedCards = (cards ?? []).filter((c) => !c.is_active);

  const totalOutstanding = activeCards.reduce((s, c) => s + (c.outstanding_paise || 0), 0);
  const totalLimit = activeCards.reduce((s, c) => s + (c.credit_limit_paise || 0), 0);
  const totalUtilization = totalLimit > 0 ? (totalOutstanding / totalLimit) * 100 : 0;

  const handleCreate = (form: CardFormData) => {
    createCard({
      account_id: null,
      card_name: form.card_name,
      card_type: form.card_type,
      issuer: form.issuer,
      last_four: form.last_four,
      cardholder_name: form.cardholder_name,
      credit_limit_paise: Math.round((parseFloat(form.credit_limit_rupees) || 0) * 100),
      outstanding_paise: Math.round((parseFloat(form.outstanding_rupees) || 0) * 100),
      minimum_due_paise: 0,
      billing_date: parseInt(form.billing_date) || 1,
      payment_due_date: parseInt(form.payment_due_date) || 5,
      apr: parseFloat(form.apr) || 0,
      reward_type: form.reward_type,
      linked_account_id: form.linked_account_id ? parseInt(form.linked_account_id) : null,
      card_color: '',
      card_gradient: form.card_gradient,
    });
    setDialogOpen(false);
  };

  const handleUpdate = (form: CardFormData) => {
    if (!editingCard) return;
    updateCard({
      id: editingCard.id,
      card: {
        account_id: editingCard.account_id,
        card_name: form.card_name,
        card_type: form.card_type,
        issuer: form.issuer,
        last_four: form.last_four,
        cardholder_name: form.cardholder_name,
        credit_limit_paise: Math.round((parseFloat(form.credit_limit_rupees) || 0) * 100),
        outstanding_paise: Math.round((parseFloat(form.outstanding_rupees) || 0) * 100),
        minimum_due_paise: editingCard.minimum_due_paise,
        billing_date: parseInt(form.billing_date) || 1,
        payment_due_date: parseInt(form.payment_due_date) || 5,
        apr: parseFloat(form.apr) || 0,
        reward_type: form.reward_type,
        linked_account_id: form.linked_account_id ? parseInt(form.linked_account_id) : null,
        card_color: editingCard.card_color,
        card_gradient: form.card_gradient,
      },
    });
    setEditingCard(null);
    setDialogOpen(false);
  };

  const handleDelete = (id: number) => {
    if (!confirm('Delete this card?')) return;
    deleteCard(id);
  };

  const viewTransactions = (card: CardType) => {
    window.open(`/transactions?cardId=${card.id}`, '_blank');
  };

  const openEdit = (card: CardType) => {
    setEditingCard(card);
    setDialogOpen(true);
  };

  return (
    <PageShell
      title="Credit Cards"
      subtitle={`${activeCards.length} active`}
      actions={
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="h-4 w-4 mr-2" />Add Card</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>{editingCard ? 'Edit Card' : 'Add Card'}</DialogTitle></DialogHeader>
            <CardForm initialData={editingCard ?? undefined} onSubmit={editingCard ? handleUpdate : handleCreate} onCancel={() => { setEditingCard(null); setDialogOpen(false); }} />
          </DialogContent>
        </Dialog>
      }
    >
      {/* Summary KPI */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Total Outstanding" value={formatINR(totalOutstanding)} subtext="Active cards" variant="danger" />
        <KpiCard title="Total Limit" value={formatINR(totalLimit)} subtext="Credit limit" />
        <KpiCard title="Utilization" value={formatPercent(totalUtilization)} subtext="Used / limit" variant={totalUtilization > 70 ? 'danger' : totalUtilization > 30 ? 'warning' : 'success'} />
        <KpiCard title="Min Due (est.)" value={formatINR(activeCards.reduce((s, c) => s + (c.minimum_due_paise || 0), 0))} subtext="This cycle" />
      </div>

      {/* Active Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {activeCards.map((card) => (
          <CardVisual key={card.id} card={card} onEdit={openEdit} onDelete={handleDelete} onViewTx={viewTransactions} />
        ))}
      </div>

      {/* Closed Cards */}
      {closedCards.length > 0 && (
        <details className="rounded-xl border bg-card">
          <summary className="px-5 py-3 text-sm font-semibold cursor-pointer">Closed Cards ({closedCards.length})</summary>
          <div className="px-5 pb-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 opacity-60">
            {closedCards.map((card) => (
              <CardVisual key={card.id} card={card} onEdit={openEdit} onDelete={handleDelete} onViewTx={viewTransactions} />
            ))}
          </div>
        </details>
      )}
    </PageShell>
  );
}

// ============================================================
// Card Form
// ============================================================

function CardForm({ initialData, onSubmit, onCancel }: { initialData?: CardType; onSubmit: (data: CardFormData) => void; onCancel: () => void }) {
  const [formData, setFormData] = useState<CardFormData>(() => {
    const c = initialData;
    return {
      card_name: c?.card_name || '',
      card_type: (c?.card_type as typeof CARD_TYPES[number]['value']) || 'visa',
      issuer: c?.issuer || '',
      last_four: c?.last_four || '',
      cardholder_name: c?.cardholder_name || '',
      credit_limit_rupees: c?.credit_limit_paise ? String(c.credit_limit_paise / 100) : '',
      outstanding_rupees: c?.outstanding_paise ? String(c.outstanding_paise / 100) : '',
      billing_date: c?.billing_date ? String(c.billing_date) : '1',
      payment_due_date: c?.payment_due_date ? String(c.payment_due_date) : '5',
      apr: c?.apr ? String(c.apr) : '',
      reward_type: c?.reward_type || 'None',
      linked_account_id: c?.linked_account_id ? String(c.linked_account_id) : '',
      card_gradient: c ? c.card_gradient : 'from-slate-700 to-slate-900',
      is_active: c?.is_active ?? true,
    };
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="card_name">Card Name</Label>
          <Input id="card_name" value={formData.card_name} onChange={(e) => setFormData({ ...formData, card_name: e.target.value })} required />
        </div>
        <div>
          <Label htmlFor="issuer">Bank / Issuer</Label>
          <Input id="issuer" value={formData.issuer} onChange={(e) => setFormData({ ...formData, issuer: e.target.value })} required />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="last_four">Last 4 Digits</Label>
          <Input id="last_four" value={formData.last_four} onChange={(e) => setFormData({ ...formData, last_four: e.target.value })} maxLength={4} required />
        </div>
        <div>
          <Label htmlFor="cardholder_name">Cardholder Name</Label>
          <Input id="cardholder_name" value={formData.cardholder_name} onChange={(e) => setFormData({ ...formData, cardholder_name: e.target.value })} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="credit_limit_rupees">Credit Limit (₹)</Label>
          <Input id="credit_limit_rupees" type="number" value={formData.credit_limit_rupees} onChange={(e) => setFormData({ ...formData, credit_limit_rupees: e.target.value })} required />
        </div>
        <div>
          <Label htmlFor="outstanding_rupees">Current Outstanding (₹)</Label>
          <Input id="outstanding_rupees" type="number" value={formData.outstanding_rupees} onChange={(e) => setFormData({ ...formData, outstanding_rupees: e.target.value })} required />
        </div>
      </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="billing_date">Statement Date (Day)</Label>
            <Input id="billing_date" type="number" min="1" max="31" value={formData.billing_date} onChange={(e) => setFormData({ ...formData, billing_date: e.target.value })} required />
          </div>
          <div>
            <Label htmlFor="payment_due_date">Payment Due Date (Day)</Label>
            <Input id="payment_due_date" type="number" min="1" max="31" value={formData.payment_due_date} onChange={(e) => setFormData({ ...formData, payment_due_date: e.target.value })} required />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="linked_account_id">Linked Account (optional)</Label>
            <Input id="linked_account_id" type="number" value={formData.linked_account_id} onChange={(e) => setFormData({ ...formData, linked_account_id: e.target.value })} placeholder="Account ID" />
          </div>
          <div>
            <Label>Card Design</Label>
            <div className="flex flex-wrap gap-2">
              {CARD_GRADIENTS.map((grad) => (
                <button key={grad.value} type="button" className={`w-10 h-10 rounded-full bg-gradient-to-br ${grad.value} border-2 transition-all ${formData.card_gradient === grad.value ? 'border-foreground scale-110 shadow-md' : 'border-transparent'}`} onClick={() => setFormData({ ...formData, card_gradient: grad.value })} title={grad.name} />
              ))}
            </div>
          </div>
        </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="apr">APR / Interest Rate (%)</Label>
          <Input id="apr" type="number" step="0.01" value={formData.apr} onChange={(e) => setFormData({ ...formData, apr: e.target.value })} placeholder="e.g., 24.5" />
        </div>
        <div>
          <Label htmlFor="reward_type">Reward Type</Label>
          <Select value={formData.reward_type} onValueChange={(v) => setFormData({ ...formData, reward_type: v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="None">None</SelectItem>
              <SelectItem value="Cashback">Cashback</SelectItem>
              <SelectItem value="Points">Points</SelectItem>
              <SelectItem value="Miles">Miles</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

        <div className="flex items-center gap-2">
          <input id="is_active" type="checkbox" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} className="rounded" />
          <Label htmlFor="is_active">Active</Label>
        </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
        <Button type="submit">{initialData ? 'Update Card' : 'Add Card'}</Button>
      </div>
    </form>
  );
}