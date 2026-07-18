"use client";

/**
 * Investments Page - Personal Finance MVP v1.0.0
 * ==============================================
 * 
 * Features:
 * - List all active investments with summary
 * - Portfolio allocation chart
 * - Gain/loss tracking
 */

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Pencil, Trash2, TrendingUp, AlertCircle, PieChart, BarChart3 } from "lucide-react";
import { formatINR } from "@/lib/utils/format";
import { useInvestments, useCreateInvestment, useUpdateInvestment, useDeleteInvestment } from "@/lib/hooks/use-investments";
import type { InvestmentSummaryModel } from "@/lib/models/investments";

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
  investment: InvestmentSummaryModel; 
  onEdit: (investment: InvestmentSummaryModel) => void;
  onDelete: (id: string) => void;
}) {
  const isGain = investment.gainPaise >= 0;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <TrendingUp className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <h3 className="font-medium text-sm">{investment.name}</h3>
              <p className="text-xs text-gray-500">{investment.type.replace('_', ' ')}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={() => onEdit(investment)}>
              <Pencil className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onDelete(investment.id.toString())}>
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Current Value</span>
            <span className="text-lg font-semibold">{formatINR(investment.currentPaise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Invested</span>
            <span className="text-sm font-medium">{formatINR(investment.investedPaise)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">P&L</span>
            <span className={`text-sm font-medium ${isGain ? 'text-green-600' : 'text-red-600'}`}>
              {isGain ? '+' : ''}{formatINR(investment.gainPaise)} ({investment.gainPercent >= 0 ? '+' : ''}{investment.gainPercent.toFixed(1)}%)
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function InvestmentForm({ 
  initialData, 
  onSubmit, 
  onCancel 
}: { 
  initialData?: InvestmentSummaryModel; 
  onSubmit: (data: InvestmentFormData) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<InvestmentFormData>({
    name: initialData?.name || "",
    investment_type: (initialData?.type as any) || "mutual_fund",
    invested_paise: initialData ? (initialData.investedPaise / 100).toString() : "",
    current_value_paise: initialData ? (initialData.currentPaise / 100).toString() : "",
    as_of_date: initialData?.isActive ? "" : "",
    platform: "",
    units: "",
    notes: "",
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
    <Card>
      <CardContent className="p-4">
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
                  <span className="text-sm font-medium">{formatINR(value)}</span>
                  <span className="text-xs text-gray-500 ml-2">{percent.toFixed(1)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
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
  const [editingInvestment, setEditingInvestment] = useState<InvestmentSummaryModel | null>(null);

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

  const handleEditInvestment = (investment: InvestmentSummaryModel) => {
    setEditingInvestment(investment);
    setDialogOpen(true);
  };

  const handleAddNew = () => {
    setEditingInvestment(null);
    setDialogOpen(true);
  };

  // Calculate totals
  const totalInvested = data?.totalInvestedPaise || 0;
  const totalCurrent = data?.totalCurrentPaise || 0;
  const totalGain = data?.totalGainPaise || 0;
  const gainPercent = data ? (totalCurrent - totalInvested) / totalInvested * 100 : 0;

  // Calculate allocation by type
  const allocationByType: Record<string, number> = {}
  data?.investments.forEach(inv => {
    allocationByType[inv.type] = (allocationByType[inv.type] || 0) + inv.currentPaise
  })

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Investments</h1>
          <p className="text-gray-500 text-sm">Track your portfolio and investments</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleAddNew}>
              <Plus className="mr-2 h-4 w-4" />
              Add Investment
            </Button>
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
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-gray-500" />
              <span className="text-gray-600">Total Invested</span>
            </div>
            <p className="text-2xl font-bold mt-2">{formatINR(totalInvested)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-gray-500" />
              <span className="text-gray-600">Current Value</span>
            </div>
            <p className="text-2xl font-bold mt-2">{formatINR(totalCurrent)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Total P&L</span>
            </div>
            <p className={`text-2xl font-bold mt-2 ${totalGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {totalGain >= 0 ? '+' : ''}{formatINR(totalGain)} ({gainPercent >= 0 ? '+' : ''}{gainPercent.toFixed(1)}%)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {/* Investments Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Investments List */}
        <div className="lg:col-span-2">
          {data?.investments.length === 0 ? (
            <Card className="p-6 text-center">
              <p className="text-gray-500">No investments added. Add your first investment above.</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data?.investments.map((investment) => (
                <InvestmentCard
                  key={investment.id}
                  investment={investment}
                  onEdit={handleEditInvestment}
                  onDelete={handleDeleteInvestment}
                />
              ))}
            </div>
          )}
        </div>

        {/* Allocation Chart */}
        <div>
          <AllocationChart allocation={allocationByType} />
        </div>
      </div>
    </div>
  );
}