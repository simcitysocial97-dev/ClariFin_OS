/**
 * Investments Page - Stage 8E-C2 Production Visual System Migration
 *
 * Portfolio Explorer Surface - Main analysis surface for investments.
 * Shell provides: Header, Toolbar, Breadcrumbs, Selection Summary, Evidence Drawer.
 *
 * Migrated: Wrapped in Surface/Panel primitives, removed legacy padding.
 * Updated: Using MoneyValue primitive and semantic colors.
 */

"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Pencil, Trash2, TrendingUp, AlertCircle, PieChart, BarChart3 } from "lucide-react";
import { useInvestments, useCreateInvestment, useUpdateInvestment, useDeleteInvestment, type Investment } from "@/lib/hooks/use-investments";
import { Surface } from "@/components/primitives/surface/surface";
import { Panel, PanelHeader, PanelBody } from "@/components/primitives/panel/panel";
import { Stack } from "@/components/primitives/layout/stack";
import { Grid } from "@/components/primitives/layout/grid";
import { MoneyValue } from "@/components/primitives/data-display/money-value";
import { commandCenterRuntime } from "@/lib/command-center";

// ============================================================
// Form Types
// ============================================================

interface InvestmentFormData {
  name: string;
  investment_type: "mutual_fund" | "stock" | "fd" | "gold_etf" | "ppf" | "nps" | "bonds" | "crypto";
  invested_paise: string;
  current_value_paise: string;
  as_of_date: string;
  platform?: string;
  units?: string;
  notes?: string;
}

// ============================================================
// Components
// ============================================================

function InvestmentCard({ investment, onEdit, onDelete }: { 
  investment: Investment; 
  onEdit: (investment: Investment) => void;
  onDelete: (id: string) => void;
}) {
  const gain = investment.current_value_paise - investment.invested_paise;
  const gainPercent = investment.invested_paise > 0 ? (gain / investment.invested_paise) * 100 : 0;
  const isGain = gain >= 0;

  return (
    <Surface variant="raised" density="none" className="p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[var(--surface-raised)] rounded-lg">
            <TrendingUp className="h-5 w-5 text-[var(--text-secondary)]" />
          </div>
          <div>
            <h3 className="font-medium text-sm">{investment.name}</h3>
            <p className="text-xs text-[var(--text-tertiary)]">{investment.investment_type.replace('_', ' ')}</p>
            <span className="inline-block mt-1 text-xs bg-[var(--surface-raised)] px-2 py-0.5 rounded">
              {investment.platform || "Self"}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={() => onEdit(investment)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete(investment.id.toString())}>
            <Trash2 className="h-4 w-4 text-[var(--color-negative-600)]" />
          </Button>
        </div>
      </div>
      <div className="mt-3 pt-2 border-t space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-[var(--text-tertiary)]">Current Value</span>
          <MoneyValue paise={investment.current_value_paise} variant="default" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-[var(--text-tertiary)]">Invested</span>
          <MoneyValue paise={investment.invested_paise} variant="default" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-[var(--text-tertiary)]">P&L</span>
          <span className={`text-sm font-medium ${isGain ? 'text-[var(--color-positive-600)]' : 'text-[var(--color-negative-600)]'}`}>
            {isGain ? '+' : ''}<MoneyValue paise={gain} variant="default" sign="auto" /> ({gainPercent.toFixed(1)}%)
          </span>
        </div>
      </div>
    </Surface>
  );
}

function InvestmentForm({ 
  initialData, 
  onSubmit, 
  onCancel 
}: { 
  initialData?: Investment; 
  onSubmit: (data: InvestmentFormData) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<InvestmentFormData>({
    name: initialData?.name || "",
    investment_type: (initialData?.investment_type as any) || "mutual_fund",
    invested_paise: initialData ? (initialData.invested_paise / 100).toString() : "",
    current_value_paise: initialData ? (initialData.current_value_paise / 100).toString() : "",
    as_of_date: initialData?.as_of_date || "",
    platform: initialData?.platform || "",
    units: initialData?.units ? initialData.units.toString() : "",
    notes: initialData?.notes || "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="name">Investment Name</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="e.g., Nifty 50 Index Fund"
          required
        />
      </div>
      <div>
        <Label htmlFor="investment_type">Type</Label>
        <Select
          value={formData.investment_type}
          onValueChange={(value: any) => setFormData({ ...formData, investment_type: value })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="mutual_fund">Mutual Fund</SelectItem>
            <SelectItem value="stock">Stock</SelectItem>
            <SelectItem value="fd">Fixed Deposit</SelectItem>
            <SelectItem value="gold_etf">Gold ETF</SelectItem>
            <SelectItem value="ppf">PPF</SelectItem>
            <SelectItem value="nps">NPS</SelectItem>
            <SelectItem value="bonds">Bonds</SelectItem>
            <SelectItem value="crypto">Crypto</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label htmlFor="invested_paise">Invested Amount (₹)</Label>
        <Input
          id="invested_paise"
          type="number"
          step="0.01"
          value={formData.invested_paise}
          onChange={(e) => setFormData({ ...formData, invested_paise: e.target.value })}
          placeholder="0.00"
          required
        />
      </div>
      <div>
        <Label htmlFor="current_value_paise">Current Value (₹)</Label>
        <Input
          id="current_value_paise"
          type="number"
          step="0.01"
          value={formData.current_value_paise}
          onChange={(e) => setFormData({ ...formData, current_value_paise: e.target.value })}
          placeholder="0.00"
          required
        />
      </div>
      <div>
        <Label htmlFor="as_of_date">As of Date</Label>
        <Input
          id="as_of_date"
          type="date"
          value={formData.as_of_date}
          onChange={(e) => setFormData({ ...formData, as_of_date: e.target.value })}
          required
        />
      </div>
      <div>
        <Label htmlFor="platform">Platform (optional)</Label>
        <Input
          id="platform"
          value={formData.platform}
          onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
          placeholder="e.g., Zerodha, Groww"
        />
      </div>
      <div>
        <Label htmlFor="units">Units (optional)</Label>
        <Input
          id="units"
          type="number"
          step="0.001"
          value={formData.units}
          onChange={(e) => setFormData({ ...formData, units: e.target.value })}
          placeholder="0"
        />
      </div>
      <div>
        <Label htmlFor="notes">Notes (optional)</Label>
        <Input
          id="notes"
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          placeholder="Any notes"
        />
      </div>
      <div className="flex gap-2 pt-2">
        <Button type="submit" className="flex-1">
          {initialData ? "Update Investment" : "Add Investment"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ============================================================
// Allocation Chart
// ============================================================

function AllocationChart({ allocation }: { allocation: Record<string, number> }) {
  const total = Object.values(allocation).reduce((sum, v) => sum + v, 0);
  const colors = ['#6366F1', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#3B82F6', '#EF4444'];
  
  return (
    <Surface variant="raised" density="none" className="p-4">
      <h3 className="font-medium mb-3 flex items-center gap-2">
        <PieChart className="h-4 w-4" />
        Portfolio Allocation
      </h3>
      <div className="space-y-2">
        {Object.entries(allocation).map(([type, value], index) => {
          const percent = total > 0 ? (value / total) * 100 : 0;
          return (
            <div key={type} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="text-sm">{type.replace('_', ' ')}</span>
              </div>
              <div className="text-right">
                <MoneyValue paise={value} variant="default" />
                <span className="text-xs text-[var(--text-tertiary)] ml-2">{percent.toFixed(1)}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </Surface>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function InvestmentsPage() {
  const { data, isLoading, error } = useInvestments();
  const createInvestmentMutation = useCreateInvestment();
  const updateInvestmentMutation = useUpdateInvestment();
  const deleteInvestmentMutation = useDeleteInvestment();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingInvestment, setEditingInvestment] = useState<Investment | null>(null);

  const handleCreateInvestment = async (formData: InvestmentFormData) => {
    try {
      await createInvestmentMutation.mutateAsync({
        name: formData.name,
        investment_type: formData.investment_type,
        invested_paise: Math.round(parseFloat(formData.invested_paise) * 100),
        current_value_paise: Math.round(parseFloat(formData.current_value_paise) * 100),
        as_of_date: formData.as_of_date,
        platform: formData.platform || undefined,
        units: formData.units ? parseFloat(formData.units) : undefined,
        notes: formData.notes || undefined,
      });
      setDialogOpen(false);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleUpdateInvestment = async (formData: InvestmentFormData) => {
    if (!editingInvestment) return;
    try {
      await updateInvestmentMutation.mutateAsync({
        id: editingInvestment.id.toString(),
        invested_paise: Math.round(parseFloat(formData.invested_paise) * 100),
        current_value_paise: Math.round(parseFloat(formData.current_value_paise) * 100),
        as_of_date: formData.as_of_date,
        platform: formData.platform || undefined,
        units: formData.units ? parseFloat(formData.units) : undefined,
        notes: formData.notes || undefined,
      });
      setEditingInvestment(null);
      setDialogOpen(false);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleDeleteInvestment = async (id: string) => {
    if (!confirm("Are you sure you want to delete this investment?")) return;
    try {
      await deleteInvestmentMutation.mutateAsync(id);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleEditInvestment = (investment: Investment) => {
    setEditingInvestment(investment);
    setDialogOpen(true);
  };

  // Build view model for shared runtime
  const viewModels = useMemo(() => ({
    investments: {
      investments: data?.investments || [],
      summary: data?.summary,
    },
  }), [data]);

  // Register workspace with CommandCenterRuntime on mount
  useEffect(() => {
    // Build graph for shared runtime
    commandCenterRuntime.build(viewModels);

    // Register workspace actions
    const workspaceRegistration = {
      name: 'investments' as const,
      label: 'Investments',
      icon: 'trending-up',
      deepLink: '/investments',
      viewModelKey: 'investments',
      description: 'Investment portfolio and holdings',
      defaultSurface: 'TABLE' as const,
      graphAdapter: 'investments',
      supportedCommands: ['add', 'edit', 'delete', 'refresh'],
      supportedFilters: ['search'],
      supportedSelections: ['investment'],
      inspectorSections: ['context', 'allocation', 'related'],
      keyboardShortcuts: {
        'a': 'add',
        'r': 'refresh',
      },
    };

    commandCenterRuntime.registerWorkspace(workspaceRegistration);

    return () => {
      commandCenterRuntime.unregisterWorkspace('investments');
    };
  }, [viewModels]);

  // Calculate totals
  const totalInvested = data?.summary.total_invested_paise || 0;
  const totalCurrent = data?.summary.total_current_value_paise || 0;
  const totalGain = data?.summary.total_gain_paise || 0;
  const gainPercent = data?.summary.gain_percent || 0;
  const isGain = totalGain >= 0;

  if (isLoading) {
    return (
      <Surface variant="default" density="none" className="flex flex-col h-full">
        <Panel fill>
          <PanelHeader title="Investments" />
          <PanelBody loading>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-40" />
              ))}
            </div>
          </PanelBody>
        </Panel>
      </Surface>
    );
  }

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Investments" />
        <PanelBody scrollable>
          <Stack gap={4} className="p-4">
            {/* Summary Cards */}
            <Grid gap={4} className="grid-cols-1 md:grid-cols-3">
              <Surface variant="raised" density="none" className="p-4">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-[var(--text-tertiary)]" />
                  <span className="text-[var(--text-secondary)]">Total Invested</span>
                </div>
                <MoneyValue paise={totalInvested} variant="large" />
              </Surface>
              <Surface variant="raised" density="none" className="p-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-[var(--text-tertiary)]" />
                  <span className="text-[var(--text-secondary)]">Current Value</span>
                </div>
                <MoneyValue paise={totalCurrent} variant="large" />
              </Surface>
              <Surface variant="raised" density="none" className="p-4">
                <div className="flex items-center gap-2">
                  <span className="text-[var(--text-secondary)]">Total P&L</span>
                </div>
                <span className={`text-2xl font-bold ${isGain ? 'text-[var(--color-positive-600)]' : 'text-[var(--color-negative-600)]'}`}>
                  {isGain ? '+' : ''}<MoneyValue paise={totalGain} variant="large" sign="auto" /> ({isGain ? '+' : ''}{gainPercent.toFixed(1)}%)
                </span>
              </Surface>
            </Grid>

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error.message}</AlertDescription>
              </Alert>
            )}

            {/* Investments Grid */}
            <Grid gap={4} className="grid-cols-1 lg:grid-cols-3">
              {/* Investments List */}
              <div className="lg:col-span-2">
                {data?.investments.length === 0 ? (
                  <Surface variant="raised" density="none" className="p-6 text-center">
                    <p className="text-[var(--text-tertiary)]">No investments added. Add your first investment above.</p>
                  </Surface>
                ) : (
                  <Grid gap={4} className="grid-cols-1 md:grid-cols-2">
                    {data?.investments.map((investment) => (
                      <InvestmentCard
                        key={investment.id}
                        investment={investment}
                        onEdit={handleEditInvestment}
                        onDelete={handleDeleteInvestment}
                      />
                    ))}
                  </Grid>
                )}
              </div>

              {/* Allocation Chart */}
              <div>
                <AllocationChart allocation={data?.summary.allocation_by_type || {}} />
              </div>
            </Grid>
          </Stack>
        </PanelBody>
      </Panel>

      {/* Add Investment Dialog - triggered by TopCommandBar */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogTrigger asChild>
          <button className="hidden" aria-hidden="true">
            Add Investment
          </button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingInvestment ? "Edit Investment" : "Add New Investment"}</DialogTitle>
          </DialogHeader>
          <InvestmentForm
            initialData={editingInvestment || undefined}
            onSubmit={editingInvestment ? handleUpdateInvestment : handleCreateInvestment}
            onCancel={() => {
              setEditingInvestment(null);
              setDialogOpen(false);
            }}
          />
        </DialogContent>
      </Dialog>
    </Surface>
  );
}