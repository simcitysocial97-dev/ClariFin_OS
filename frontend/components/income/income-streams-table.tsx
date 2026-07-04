"use client";

/**
 * Income Streams Table
 * ====================
 * Table component for displaying and managing income sources.
 */

import { useState } from "react";
import {
  useIncomeSources,
  useCreateIncomeSource,
  useUpdateIncomeSource,
  useDeleteIncomeSource,
} from "@/lib/hooks/use-finance-data";
import { formatPaise } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { WidgetErrorFallback } from "@/components/dashboard/widget-error-fallback";
import {
  Briefcase,
  Shield,
  AlertTriangle,
  Plus,
  Pencil,
  Trash2,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { IncomeSourceDialog } from "./income-source-dialog";
import type { IncomeSource, IncomeSourceCreate, IncomeSourceUpdate } from "@/types/income";

// ============================================================
// Constants
// ============================================================

const STABILITY_CONFIG = {
  high: {
    label: "High",
    color: "bg-green-100 text-green-800",
    icon: <Shield className="h-3 w-3" />,
  },
  medium: {
    label: "Medium",
    color: "bg-amber-100 text-amber-800",
    icon: <Briefcase className="h-3 w-3" />,
  },
  low: {
    label: "Low",
    color: "bg-red-100 text-red-800",
    icon: <AlertTriangle className="h-3 w-3" />,
  },
} as const;

// ============================================================
// Helper Functions
// ============================================================

function getStability(
  source: IncomeSource
): {
  level: "high" | "medium" | "low";
  label: string;
  color: string;
  icon: React.ReactNode;
} {
  // Salary is most stable
  if (source.type === "salary") {
    return { level: "high", ...STABILITY_CONFIG.high };
  }
  // Freelance and business are less stable
  if (source.type === "freelance" || source.type === "business") {
    return { level: "low", ...STABILITY_CONFIG.low };
  }
  // Rental, dividends, interest are medium
  if (
    source.type === "rental" ||
    source.type === "dividend" ||
    source.type === "interest"
  ) {
    return { level: "medium", ...STABILITY_CONFIG.medium };
  }
  return { level: "medium", ...STABILITY_CONFIG.medium };
}

// ============================================================
// Component
// ============================================================

export function IncomeStreamsTable({ className }: { className?: string }) {
  // Data fetching
  const { incomeStreams, loading, error, refetch } = useIncomeSources();

  // Mutations
  const { createIncomeSource, creating: isCreating } = useCreateIncomeSource();
  const { updateIncomeSource, updating: isUpdating } = useUpdateIncomeSource();
  const { deleteIncomeSource, deleting: isDeleting } = useDeleteIncomeSource();

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<IncomeSource | null>(null);

  // Delete confirmation state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sourceToDelete, setSourceToDelete] = useState<IncomeSource | null>(null);

  // Loading states
  const isSubmitting = isCreating || isUpdating;

  // Handlers
  const handleCreateClick = () => {
    setEditingSource(null);
    setDialogOpen(true);
  };

  const handleEditClick = (source: IncomeSource) => {
    setEditingSource(source);
    setDialogOpen(true);
  };

  const handleDeleteClick = (source: IncomeSource) => {
    setSourceToDelete(source);
    setDeleteDialogOpen(true);
  };

  const handleSubmit = async (data: IncomeSourceCreate | IncomeSourceUpdate) => {
    try {
      if (editingSource) {
        await updateIncomeSource({ id: editingSource.id, source: data as IncomeSourceUpdate });
      } else {
        await createIncomeSource(data as IncomeSourceCreate);
      }
      setDialogOpen(false);
      refetch();
    } catch (err) {
      // Error is handled by the hook
      console.error("Failed to save income source:", err);
    }
  };

  const handleConfirmDelete = async () => {
    if (!sourceToDelete) return;

    try {
      await deleteIncomeSource(sourceToDelete.id);
      setDeleteDialogOpen(false);
      setSourceToDelete(null);
      refetch();
    } catch (err) {
      // Error is handled by the hook
      console.error("Failed to delete income source:", err);
    }
  };

  // Loading state
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="h-5 w-40 bg-muted rounded animate-pulse" />
            <div className="h-9 w-32 bg-muted rounded animate-pulse" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex justify-between items-center py-2">
                <div className="h-4 w-28 bg-muted rounded animate-pulse" />
                <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                <div className="h-6 w-16 bg-muted rounded animate-pulse" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <WidgetErrorFallback
            title="Income Streams"
            error={error.message}
            onRetry={refetch}
          />
        </CardContent>
      </Card>
    );
  }

  const sources = incomeStreams ?? [];

  return (
    <>
      <Card className={className}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Briefcase className="h-4 w-4" />
              Income Streams
            </CardTitle>
            <Button size="sm" onClick={handleCreateClick}>
              <Plus className="h-4 w-4 mr-1" />
              Add Source
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {sources.length === 0 ? (
            <div className="text-center py-12">
              <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Briefcase className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">No income sources</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Add your income sources to track and analyze your earnings
              </p>
              <Button onClick={handleCreateClick}>
                <Plus className="h-4 w-4 mr-1" />
                Add Your First Income Source
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Stability</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.map((source: IncomeSource) => {
                  const stability = getStability(source);
                  return (
                    <TableRow key={source.id}>
                      <TableCell className="font-medium">{source.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {source.type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-medium text-green-600">
                        +{formatPaise(source.amount_paise)}
                      </TableCell>
                      <TableCell className="capitalize">{source.frequency}</TableCell>
                      <TableCell>
                        <Badge
                          className={cn("flex items-center gap-1 w-fit", stability.color)}
                        >
                          {stability.icon}
                          {stability.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {source.is_active ? (
                          <Badge className="bg-green-100 text-green-800">Active</Badge>
                        ) : (
                          <Badge variant="secondary">Inactive</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => handleEditClick(source)}
                            aria-label={`Edit ${source.name}`}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={() => handleDeleteClick(source)}
                            disabled={isDeleting}
                            aria-label={`Delete ${source.name}`}
                          >
                            {isDeleting && sourceToDelete?.id === source.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <IncomeSourceDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        source={editingSource}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Income Source</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{sourceToDelete?.name}</strong>? This
              action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
