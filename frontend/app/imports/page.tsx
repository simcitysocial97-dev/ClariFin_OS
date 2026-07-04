"use client";

/**
 * Imports List Page
 * =================
 * 
 * Shows all V2 statement imports with:
 * - Filters by status
 * - Table with filename, bank, created_at, status, validation reason
 * - Actions: Add Balances, Draw Bbox, Commit
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useImportsQuery } from "@/lib/hooks/use-query-finance";
import { useToast } from "@/hooks/use-toast";
import { formatPaise } from "@/lib/format";
import {
  commitV2Import,
  setImportBalances,
} from "@/lib/api/client";
import {
  FileText,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Coins,
  Crop,
  Upload,
  Loader2,
  Eye,
} from "lucide-react";
import Link from "next/link";
import type { ImportItem, ImportStatus } from "@/types/v2";

// ============================================================================
// Status Configuration
// ============================================================================

const statusConfig: Record<
  ImportStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  STAGED: { label: "Staged", variant: "outline" },
  NEEDS_REVIEW: { label: "Needs Review", variant: "secondary" },
  COMMITTED: { label: "Committed", variant: "default" },
  FAILED: { label: "Failed", variant: "destructive" },
};

function getStatusBadge(status: ImportStatus) {
  const config = statusConfig[status];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}

// ============================================================================
// Format Helpers
// ============================================================================

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function truncateFilename(filename: string, maxLength: number = 40): string {
  if (filename.length <= maxLength) return filename;
  const ext = filename.split(".").pop();
  const name = filename.substring(0, maxLength - 4);
  return `${name}...${ext ? `.${ext}` : ""}`;
}

// ============================================================================
// Add Balances Dialog
// ============================================================================

interface AddBalancesDialogProps {
  importItem: ImportItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

function AddBalancesDialog({
  importItem,
  open,
  onOpenChange,
  onSuccess,
}: AddBalancesDialogProps) {
  const { toast } = useToast();
  const [openingBalance, setOpeningBalance] = useState("");
  const [closingBalance, setClosingBalance] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!importItem) return;

    const openingPaise = Math.round(parseFloat(openingBalance) * 100);
    const closingPaise = Math.round(parseFloat(closingBalance) * 100);

    if (isNaN(openingPaise) || isNaN(closingPaise)) {
      toast({
        title: "Invalid amounts",
        description: "Please enter valid numbers",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      const result = await setImportBalances(
        importItem.id,
        openingPaise,
        closingPaise
      );

      if (result.success) {
        toast({
          title: "Balances updated",
          description: result.committed
            ? "Import validated and committed successfully"
            : "Balances updated, still needs review",
        });
        onSuccess();
        onOpenChange(false);
      } else {
        toast({
          title: "Update failed",
          description: result.error || "Failed to update balances",
          variant: "destructive",
        });
      }
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Opening & Closing Balances</DialogTitle>
          <DialogDescription>
            Enter the actual opening and closing balances from the statement.
            File: {importItem?.source_filename}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="opening" className="text-right">
              Opening
            </Label>
            <Input
              id="opening"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={openingBalance}
              onChange={(e) => setOpeningBalance(e.target.value)}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="closing" className="text-right">
              Closing
            </Label>
            <Input
              id="closing"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={closingBalance}
              onChange={(e) => setClosingBalance(e.target.value)}
              className="col-span-3"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            type="submit"
            onClick={handleSubmit}
            disabled={submitting || !openingBalance || !closingBalance}
          >
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Update & Validate
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Import Row Component
// ============================================================================

interface ImportRowProps {
  importItem: ImportItem;
  onAddBalances: (item: ImportItem) => void;
  onCommit: (item: ImportItem) => void;
  committing: boolean;
}

function ImportRow({ importItem, onAddBalances, onCommit, committing }: ImportRowProps) {
  const canAddBalances = importItem.status === "NEEDS_REVIEW";
  const canDrawBbox = importItem.status === "NEEDS_REVIEW" || importItem.status === "FAILED";
  const canCommit = importItem.status === "STAGED" || importItem.status === "NEEDS_REVIEW";

  // Validation reason text
  let validationReason = "";
  if (importItem.status === "NEEDS_REVIEW") {
    if (importItem.error?.includes("BBOX_REQUIRED")) {
      validationReason = "Table bbox required";
    } else if (!importItem.opening_balance_paise && !importItem.closing_balance_paise) {
      validationReason = "Missing balances";
    } else if (importItem.delta_paise !== null && importItem.delta_paise !== 0) {
      validationReason = `Balance mismatch ${formatPaise(importItem.delta_paise)}`;
    } else {
      validationReason = "Requires review";
    }
  } else if (importItem.status === "FAILED") {
    validationReason = importItem.error || "Extraction failed";
  }

  return (
    <tr className="border-b border-border/50 hover:bg-muted/50 transition-colors">
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span
            className="font-medium truncate max-w-[200px]"
            title={importItem.source_filename}
          >
            {truncateFilename(importItem.source_filename)}
          </span>
        </div>
      </td>
      <td className="py-3 px-4 text-sm">{importItem.bank}</td>
      <td className="py-3 px-4 text-sm text-muted-foreground">
        {formatDate(importItem.created_at)}
      </td>
      <td className="py-3 px-4">{getStatusBadge(importItem.status)}</td>
      <td className="py-3 px-4 text-sm text-muted-foreground">
        {importItem.transaction_count || 0}
      </td>
      <td className="py-3 px-4 text-sm">
        {validationReason ? (
          <span className="text-amber-600 dark:text-amber-400">{validationReason}</span>
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onAddBalances(importItem)}
            disabled={!canAddBalances}
            title={canAddBalances ? "Add opening/closing balances" : "Not needed"}
          >
            <Coins className="h-3 w-3 mr-1" />
            Balances
          </Button>
          <Link href={`/import?reextract=${importItem.id}`}>
            <Button
              variant="outline"
              size="sm"
              disabled={!canDrawBbox}
              title={canDrawBbox ? "Draw bbox and retry extraction" : "Not available"}
            >
              <Crop className="h-3 w-3 mr-1" />
              Draw Bbox
            </Button>
          </Link>
          <Button
            variant="default"
            size="sm"
            onClick={() => onCommit(importItem)}
            disabled={!canCommit || committing}
            title={canCommit ? "Commit to database" : "Not ready to commit"}
          >
            {committing ? (
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            ) : (
              <CheckCircle2 className="h-3 w-3 mr-1" />
            )}
            Commit
          </Button>
          {importItem.status === "COMMITTED" && (
            <Link href={`/transactions?statement_id=${importItem.id}`}>
              <Button
                variant="outline"
                size="sm"
                title="View imported transactions"
              >
                <Eye className="h-3 w-3 mr-1" />
                View
              </Button>
            </Link>
          )}
        </div>
      </td>
    </tr>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function ImportsPage() {
  const { toast } = useToast();
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [selectedImport, setSelectedImport] = useState<ImportItem | null>(null);
  const [balancesDialogOpen, setBalancesDialogOpen] = useState(false);
  const [committingId, setCommittingId] = useState<string | null>(null);

  const statusParam = statusFilter === "ALL" ? undefined : statusFilter as "STAGED" | "NEEDS_REVIEW" | "COMMITTED" | "FAILED";
  const { data, loading: isLoading, error, refetch } = useImportsQuery({
    status: statusParam,
    page: 1,
    per_page: 50,
  });

  const imports = data?.items || [];

  const handleAddBalances = (item: ImportItem) => {
    setSelectedImport(item);
    setBalancesDialogOpen(true);
  };

  const handleCommit = async (item: ImportItem) => {
    setCommittingId(item.id);
    try {
      const result = await commitV2Import(item.id, "Self");
      if (result.success) {
        toast({
          title: "Import committed",
          description: `Inserted ${result.inserted} transactions`,
        });
        refetch();
      } else {
        toast({
          title: "Commit failed",
          description: result.error || "Failed to commit import",
          variant: "destructive",
        });
      }
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setCommittingId(null);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Statement Imports</h1>
          <p className="text-muted-foreground mt-1">
            Manage and review your PDF statement imports
          </p>
        </div>
        <Link href="/import">
          <Button>
            <Upload className="h-4 w-4 mr-2" />
            New Import
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Status:</span>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All</SelectItem>
                  <SelectItem value="COMMITTED">Committed</SelectItem>
                  <SelectItem value="NEEDS_REVIEW">Needs Review</SelectItem>
                  <SelectItem value="FAILED">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader className="pb-0">
          <CardTitle className="text-lg">
            Imports ({data?.total || 0})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Loading imports...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-4" />
              <p className="text-destructive">{error.message}</p>
              <Button variant="outline" className="mt-4" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          ) : imports.length === 0 ? (
            <div className="p-8 text-center">
              <FileText className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
              <p className="text-muted-foreground">No imports found</p>
              <p className="text-muted-foreground text-sm mt-1">
                {statusFilter !== "ALL"
                  ? `No imports with status "${statusConfig[statusFilter as ImportStatus]?.label || statusFilter}"`
                  : "Upload a PDF statement to get started"}
              </p>
              <Link href="/import">
                <Button className="mt-4">
                  <Upload className="h-4 w-4 mr-2" />
                  Import Statement
                </Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left py-3 px-4 text-sm font-medium">Filename</th>
                    <th className="text-left py-3 px-4 text-sm font-medium">Bank</th>
                    <th className="text-left py-3 px-4 text-sm font-medium">Created</th>
                    <th className="text-left py-3 px-4 text-sm font-medium">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-medium">Transactions</th>
                    <th className="text-left py-3 px-4 text-sm font-medium">Reason</th>
                    <th className="text-left py-3 px-4 text-sm font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {imports.map((importItem) => (
                    <ImportRow
                      key={importItem.id}
                      importItem={importItem}
                      onAddBalances={handleAddBalances}
                      onCommit={handleCommit}
                      committing={committingId === importItem.id}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Balances Dialog */}
      <AddBalancesDialog
        importItem={selectedImport}
        open={balancesDialogOpen}
        onOpenChange={setBalancesDialogOpen}
        onSuccess={refetch}
      />
    </div>
  );
}
