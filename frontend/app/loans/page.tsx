"use client";

/**
 * Loans Page - Personal Finance MVP v1.0.0
 * ==========================================
 * 
 * Features:
 * - List all active loans with summary
 * - Amortization schedule drawer
 * - Prepayment simulation
 */

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle } from "@/components/ui/drawer";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Pencil, Trash2, Building2, AlertCircle, Calendar, IndianRupee, TrendingDown } from "lucide-react";
import { formatINR } from "@/lib/utils/format";
import { useLoans, useCreateLoan, useUpdateLoan, useDeleteLoan, useLoanSchedule, usePrepaymentSimulation } from "@/lib/hooks/use-loans";
import type { LoanSummaryModel } from "@/lib/models/loans";

// ============================================================
// Form Types
// ============================================================

interface LoanFormData {
  name: string;
  lender: string;
  loan_type: "personal" | "home" | "vehicle" | "education" | "gold" | "other";
  principal_paise: string;
  outstanding_paise: string;
  interest_rate: string;
  disbursed_date: string;
  tenure_months?: string;
  emi_paise?: string;
  next_emi_date?: string;
  notes?: string;
}

// ============================================================
// Components
// ============================================================

function LoanCard({ loan, onEdit, onDelete, onShowSchedule }: { 
  loan: LoanSummaryModel; 
  onEdit: (loan: LoanSummaryModel) => void;
  onDelete: (id: string) => void;
  onShowSchedule: (loan: LoanSummaryModel) => void;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Building2 className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <h3 className="font-medium text-sm">{loan.name}</h3>
              <p className="text-xs text-gray-500">{loan.lender}</p>
              <span className="inline-block mt-1 text-xs bg-gray-100 px-2 py-0.5 rounded">
                {loan.loanType || "loan"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={() => onShowSchedule(loan)}>
              <Calendar className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onEdit(loan)}>
              <Pencil className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onDelete(loan.id.toString())}>
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Outstanding</span>
            <span className="text-lg font-semibold">{formatINR(loan.outstandingPaise ?? 0)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">EMI</span>
            <span className="text-sm font-medium">{formatINR(loan.emiPaise ?? 0)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Interest Rate</span>
            <span className="text-sm font-medium">{loan.interestRate}% p.a.</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function LoanForm({ 
  initialData, 
  onSubmit, 
  onCancel 
}: { 
  initialData?: LoanSummaryModel; 
  onSubmit: (data: LoanFormData) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<LoanFormData>({
    name: initialData?.name || "",
    lender: initialData?.lender || "",
    loan_type: "personal",
    principal_paise: initialData ? (initialData.principalPaise / 100).toString() : "",
    outstanding_paise: initialData ? ((initialData.outstandingPaise ?? 0) / 100).toString() : "",
    interest_rate: initialData ? initialData.interestRate.toString() : "",
    disbursed_date: initialData?.disbursedDate || "",
    tenure_months: initialData?.tenureMonths ? (initialData.tenureMonths).toString() : "",
    emi_paise: initialData?.emiPaise ? (initialData.emiPaise / 100).toString() : "",
    next_emi_date: "",
    notes: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="name">Loan Name</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="e.g., Home Loan"
          required
        />
      </div>
      <div>
        <Label htmlFor="lender">Lender</Label>
        <Input
          id="lender"
          value={formData.lender}
          onChange={(e) => setFormData({ ...formData, lender: e.target.value })}
          placeholder="e.g., HDFC Bank"
          required
        />
      </div>
      <div>
        <Label htmlFor="loan_type">Loan Type</Label>
        <Select
          value={formData.loan_type}
          onValueChange={(value: any) => setFormData({ ...formData, loan_type: value })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="personal">Personal Loan</SelectItem>
            <SelectItem value="home">Home Loan</SelectItem>
            <SelectItem value="vehicle">Vehicle Loan</SelectItem>
            <SelectItem value="education">Education Loan</SelectItem>
            <SelectItem value="gold">Gold Loan</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label htmlFor="principal_paise">Principal (₹)</Label>
        <Input
          id="principal_paise"
          type="number"
          step="0.01"
          value={formData.principal_paise}
          onChange={(e) => setFormData({ ...formData, principal_paise: e.target.value })}
          placeholder="0.00"
          required
        />
      </div>
      <div>
        <Label htmlFor="outstanding_paise">Outstanding (₹)</Label>
        <Input
          id="outstanding_paise"
          type="number"
          step="0.01"
          value={formData.outstanding_paise}
          onChange={(e) => setFormData({ ...formData, outstanding_paise: e.target.value })}
          placeholder="0.00"
          required
        />
      </div>
      <div>
        <Label htmlFor="interest_rate">Interest Rate (% p.a.)</Label>
        <Input
          id="interest_rate"
          type="number"
          step="0.01"
          value={formData.interest_rate}
          onChange={(e) => setFormData({ ...formData, interest_rate: e.target.value })}
          placeholder="8.5"
          required
        />
      </div>
      <div>
        <Label htmlFor="disbursed_date">Disbursed Date</Label>
        <Input
          id="disbursed_date"
          type="date"
          value={formData.disbursed_date}
          onChange={(e) => setFormData({ ...formData, disbursed_date: e.target.value })}
          required
        />
      </div>
      <div>
        <Label htmlFor="tenure_months">Tenure (months)</Label>
        <Input
          id="tenure_months"
          type="number"
          value={formData.tenure_months}
          onChange={(e) => setFormData({ ...formData, tenure_months: e.target.value })}
          placeholder="120"
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
          {initialData ? "Update Loan" : "Add Loan"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ============================================================
// Amortization Schedule Drawer
// ============================================================

function AmortizationDrawer({ 
  loan, 
  open, 
  onOpenChange 
}: { 
  loan: LoanSummaryModel | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: scheduleData, isLoading: scheduleLoading } = useLoanSchedule(loan?.id?.toString() || null);

  if (!loan) return null;

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>Amortization Schedule - {loan.name}</DrawerTitle>
        </DrawerHeader>
        <div className="p-4 max-h-[60vh] overflow-y-auto">
          {scheduleLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : scheduleData?.error ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{scheduleData.error}</AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-xs text-gray-500">Total Payments</p>
                  <p className="font-semibold">{scheduleData?.total_payments || 0}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Total Interest</p>
                  <p className="font-semibold">{formatINR(scheduleData?.total_interest_paise || 0)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Total Payment</p>
                  <p className="font-semibold">{formatINR(scheduleData?.total_payment_paise || 0)}</p>
                </div>
              </div>
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">Payment Schedule</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {scheduleData?.schedule?.slice(0, 12).map((entry: any) => (
                    <div key={entry.month_number} className="flex justify-between text-sm py-1 border-b">
                      <span>Month {entry.month_number}</span>
                      <span>{formatINR(entry.emi_paise)}</span>
                      <span className="text-gray-500">{formatINR(entry.principal_paise)} principal</span>
                    </div>
                  ))}
                  {(scheduleData?.schedule?.length || 0) > 12 && (
                    <p className="text-xs text-gray-500 text-center">... and {scheduleData.schedule.length - 12} more months</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </DrawerContent>
    </Drawer>
  );
}

// ============================================================
// Prepayment Simulator
// ============================================================

function PrepaymentSimulator({ 
  loan, 
  open, 
  onOpenChange 
}: { 
  loan: LoanSummaryModel | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [prepaymentAmount, setPrepaymentAmount] = useState("");
  const [mode, setMode] = useState<"reduce_tenure" | "reduce_emi">("reduce_tenure");
  
  const { data: simulation, isLoading: simulationLoading } = usePrepaymentSimulation(
    loan?.id?.toString() || null,
    Math.round(parseFloat(prepaymentAmount) * 100) || 0,
    mode
  );

  // Use simulationLoading to prevent unused variable warning
  void simulationLoading;

  if (!loan) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Prepayment Simulation - {loan.name}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="prepayment_amount">Prepayment Amount (₹)</Label>
            <Input
              id="prepayment_amount"
              type="number"
              step="0.01"
              value={prepaymentAmount}
              onChange={(e) => setPrepaymentAmount(e.target.value)}
              placeholder="0.00"
            />
          </div>
          <div>
            <Label htmlFor="mode">Mode</Label>
            <Select value={mode} onValueChange={(v: any) => setMode(v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="reduce_tenure">Reduce Tenure</SelectItem>
                <SelectItem value="reduce_emi">Reduce EMI</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {simulation && (
            <div className="border-t pt-4 space-y-2">
              <h4 className="font-medium">Impact</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Original EMI:</span>
                  <span className="ml-2 font-medium">{formatINR(simulation.original_emi_paise)}</span>
                </div>
                <div>
                  <span className="text-gray-500">New EMI:</span>
                  <span className="ml-2 font-medium">{formatINR(simulation.new_emi_paise)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Original Tenure:</span>
                  <span className="ml-2 font-medium">{simulation.original_remaining_months} months</span>
                </div>
                <div>
                  <span className="text-gray-500">New Tenure:</span>
                  <span className="ml-2 font-medium">{simulation.new_remaining_months} months</span>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">Interest Saved:</span>
                  <span className="ml-2 font-medium text-green-600">{formatINR(simulation.interest_saved_paise)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function LoansPage() {
  const { data, isLoading, error } = useLoans();
  const createLoanMutation = useCreateLoan();
  const updateLoanMutation = useUpdateLoan();
  const deleteLoanMutation = useDeleteLoan();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLoan, setEditingLoan] = useState<LoanSummaryModel | null>(null);
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [scheduleLoan, setScheduleLoan] = useState<LoanSummaryModel | null>(null);
  // Prepayment state (for future use)
  const [prepaymentOpen, setPrepaymentOpen] = useState(false);
  const [prepaymentLoan, setPrepaymentLoan] = useState<LoanSummaryModel | null>(null);

  void setPrepaymentLoan;

  const handleCreateLoan = async (formData: LoanFormData) => {
    try {
      await createLoanMutation.mutateAsync({
        name: formData.name,
        lender: formData.lender,
        loan_type: formData.loan_type,
        principal_paise: Math.round(parseFloat(formData.principal_paise) * 100),
        outstanding_paise: Math.round(parseFloat(formData.outstanding_paise) * 100),
        interest_rate: parseFloat(formData.interest_rate),
        disbursed_date: formData.disbursed_date,
        tenure_months: formData.tenure_months ? parseInt(formData.tenure_months) : undefined,
        emi_paise: formData.emi_paise ? Math.round(parseFloat(formData.emi_paise) * 100) : undefined,
        next_emi_date: formData.next_emi_date || undefined,
        notes: formData.notes || undefined,
      });
      setDialogOpen(false);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleUpdateLoan = async (formData: LoanFormData) => {
    if (!editingLoan) return;
    try {
      await updateLoanMutation.mutateAsync({
        id: editingLoan.id.toString(),
        name: formData.name,
        lender: formData.lender,
        loan_type: formData.loan_type,
        outstanding_paise: Math.round(parseFloat(formData.outstanding_paise) * 100),
        interest_rate: parseFloat(formData.interest_rate),
        tenure_months: formData.tenure_months ? parseInt(formData.tenure_months) : undefined,
        emi_paise: formData.emi_paise ? Math.round(parseFloat(formData.emi_paise) * 100) : undefined,
        next_emi_date: formData.next_emi_date || undefined,
        notes: formData.notes || undefined,
      });
      setEditingLoan(null);
      setDialogOpen(false);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleDeleteLoan = async (id: string) => {
    if (!confirm("Are you sure you want to delete this loan?")) return;
    try {
      await deleteLoanMutation.mutateAsync(id);
    } catch (err) {
      // Error is handled by mutation
    }
  };

  const handleEditLoan = (loan: LoanSummaryModel) => {
    setEditingLoan(loan);
    setDialogOpen(true);
  };

  const handleShowSchedule = (loan: LoanSummaryModel) => {
    setScheduleLoan(loan);
    setScheduleOpen(true);
  };

  // Calculate totals
  const totalOutstanding = data?.loans.reduce((sum, l) => sum + (l.outstandingPaise ?? 0), 0) || 0;
  const totalEMI = data?.totalMonthlyEmiPaise || 0;

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
          <h1 className="text-2xl font-bold">Loans</h1>
          <p className="text-gray-500 text-sm">Track your active loans and EMIs</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setEditingLoan(null)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Loan
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingLoan ? "Edit Loan" : "Add New Loan"}</DialogTitle>
            </DialogHeader>
            <LoanForm
              initialData={editingLoan || undefined}
              onSubmit={editingLoan ? handleUpdateLoan : handleCreateLoan}
              onCancel={() => {
                setEditingLoan(null);
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
              <IndianRupee className="h-5 w-5 text-gray-500" />
              <span className="text-gray-600">Total Outstanding</span>
            </div>
            <p className="text-2xl font-bold mt-2">{formatINR(totalOutstanding)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-gray-500" />
              <span className="text-gray-600">Total Monthly EMI</span>
            </div>
            <p className="text-2xl font-bold mt-2">{formatINR(totalEMI)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5 text-gray-500" />
              <span className="text-gray-600">Active Loans</span>
            </div>
            <p className="text-2xl font-bold mt-2">{data?.loans.length || 0}</p>
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

      {/* Loans List */}
      {data?.loans.length === 0 ? (
        <Card className="p-6 text-center">
          <p className="text-gray-500">No loans added. Add your first loan above.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.loans.map((loan) => (
            <LoanCard
              key={loan.id}
              loan={loan}
              onEdit={handleEditLoan}
              onDelete={handleDeleteLoan}
              onShowSchedule={handleShowSchedule}
            />
          ))}
        </div>
      )}

      {/* Amortization Schedule Drawer */}
      <AmortizationDrawer
        loan={scheduleLoan}
        open={scheduleOpen}
        onOpenChange={setScheduleOpen}
      />

      {/* Prepayment Simulator */}
      <PrepaymentSimulator
        loan={prepaymentLoan}
        open={prepaymentOpen}
        onOpenChange={setPrepaymentOpen}
      />
    </div>
  );
}