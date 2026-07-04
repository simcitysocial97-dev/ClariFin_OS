'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Loader2,
  FileText,
  ExternalLink,
  RotateCcw,
  Trash2,
  Save,
  Eye,
  ArrowRight,
  Pencil,
  RefreshCw,
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { formatPaise } from '@/lib/format';
import type { ImportPdfResponse, ImportStatus } from '@/types/v2';
import {
  uploadV2PdfImport,
  fetchV2Import,
  commitV2Import,
  discardV2Import,
  setImportBalances,
  reextractWithBbox,
} from '@/lib/api/client';
import { PdfPreviewWithOverlay } from './pdf-preview-with-overlay';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface V2ImportStatusProps {
  file: File;
  member?: string;
  autoCommit?: boolean;
  onComplete?: () => void;
  onReset?: () => void;
}

type ImportPhase = 'uploading' | 'preview' | 'processing' | 'completed' | 'error';

const statusConfig: Record<ImportStatus, { label: string; variant: 'default' | 'destructive' | 'secondary' | 'outline'; icon: typeof CheckCircle; color: string }> = {
  STAGED: {
    label: 'Staged',
    variant: 'secondary',
    icon: FileText,
    color: 'text-blue-600 dark:text-blue-400',
  },
  NEEDS_REVIEW: {
    label: 'Needs Review',
    variant: 'secondary',
    icon: AlertTriangle,
    color: 'text-amber-600 dark:text-amber-400',
  },
  COMMITTED: {
    label: 'Committed',
    variant: 'default',
    icon: CheckCircle,
    color: 'text-green-600 dark:text-green-400',
  },
  FAILED: {
    label: 'Failed',
    variant: 'destructive',
    icon: AlertCircle,
    color: 'text-red-600 dark:text-red-400',
  },
};

/**
 * Check if balances are missing and need user input
 */
function needsBalanceInput(result: ImportPdfResponse): boolean {
  if (result.status !== 'NEEDS_REVIEW') return false;

  // Check if validation shows missing balances
  const reason = result.validation.reason?.toLowerCase() || '';
  const hasMissingBalanceReason = reason.includes('missing opening') ||
                                   reason.includes('missing closing') ||
                                   reason.includes('opening or closing');

  // Check if balances are null
  const hasNullBalances = result.validation.opening_balance_paise === null ||
                          result.validation.closing_balance_paise === null;

  return hasMissingBalanceReason || hasNullBalances;
}

/**
 * Parse rupee input string to paise
 * Returns null if invalid
 */
function parseRupeesToPaise(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;

  const parsed = parseFloat(trimmed);
  if (isNaN(parsed) || parsed < 0) return null;

  return Math.round(parsed * 100);
}

/**
 * Format paise to rupee string for input
 */
function paiseToRupeesString(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) return '';
  return (paise / 100).toFixed(2);
}

export function V2ImportStatus({
  file,
  member = 'Self',
  autoCommit = true,
  onComplete,
  onReset,
}: V2ImportStatusProps) {
  const [phase, setPhase] = useState<ImportPhase>('uploading');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<ImportPdfResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCommitting, setIsCommitting] = useState(false);
  const [isDiscarding, setIsDiscarding] = useState(false);

  // Balance input state
  const [openingBalanceInput, setOpeningBalanceInput] = useState('');
  const [closingBalanceInput, setClosingBalanceInput] = useState('');
  const [openingBalanceError, setOpeningBalanceError] = useState<string | null>(null);
  const [closingBalanceError, setClosingBalanceError] = useState<string | null>(null);
  const [isSavingBalances, setIsSavingBalances] = useState(false);
  const [balanceSaveSuccess, setBalanceSaveSuccess] = useState(false);

  // BBox drawing state
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [drawnBboxNorm, setDrawnBboxNorm] = useState<number[] | null>(null);
  const [applyToAllPages, setApplyToAllPages] = useState(true);
  const [isReextracting, setIsReextracting] = useState(false);

  // Simulate progress during upload
  useEffect(() => {
    if (phase === 'uploading') {
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 15;
        });
      }, 300);
      return () => clearInterval(interval);
    }
  }, [phase]);

  // Perform the upload
  useEffect(() => {
    let cancelled = false;

    async function performUpload() {
      try {
        setPhase('uploading');
        setProgress(10);

        const response = await uploadV2PdfImport(file, member, autoCommit);

        if (cancelled) return;

        setProgress(100);
        setResult(response);

        if (response.success) {
          // Go to preview phase first, then user can continue to completed
          setPhase('preview');
        } else {
          setPhase('error');
          setError(response.error || 'Import failed');
        }
      } catch (err) {
        if (cancelled) return;
        setPhase('error');
        setError(err instanceof Error ? err.message : 'Upload failed');
      }
    }

    performUpload();

    return () => {
      cancelled = true;
    };
  }, [file, member, autoCommit, onComplete]);

  // Initialize balance inputs when result changes and needs balance input
  useEffect(() => {
    if (result && needsBalanceInput(result)) {
      setOpeningBalanceInput(paiseToRupeesString(result.validation.opening_balance_paise));
      setClosingBalanceInput(paiseToRupeesString(result.validation.closing_balance_paise));
    }
  }, [result]);

  const handleCommit = useCallback(async () => {
    if (!result?.statement_id) return;

    setIsCommitting(true);
    try {
      const commitResult = await commitV2Import(result.statement_id, member);
      if (commitResult.success) {
        // Refresh the import status
        const updated = await fetchV2Import(result.statement_id);
        setResult({
          ...result,
          status: updated.status,
          committed: {
            inserted: commitResult.inserted,
            skipped: commitResult.skipped,
          },
        });
      } else {
        setError(commitResult.error || 'Commit failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Commit failed');
    } finally {
      setIsCommitting(false);
    }
  }, [result, member]);

  const handleDiscard = useCallback(async () => {
    if (!result?.statement_id) return;

    setIsDiscarding(true);
    try {
      await discardV2Import(result.statement_id);
      onReset?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Discard failed');
    } finally {
      setIsDiscarding(false);
    }
  }, [result, onReset]);

  const handleRefresh = useCallback(async () => {
    if (!result?.statement_id) return;

    try {
      const updated = await fetchV2Import(result.statement_id);
      setResult({
        ...result,
        status: updated.status,
        delta_paise: updated.delta_paise ?? result.delta_paise,
        validation: {
          ...result.validation,
          valid: updated.status === 'COMMITTED',
          opening_balance_paise: updated.opening_balance_paise ?? result.validation.opening_balance_paise,
          closing_balance_paise: updated.closing_balance_paise ?? result.validation.closing_balance_paise,
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refresh failed');
    }
  }, [result]);

  const handleSaveBalances = useCallback(async () => {
    if (!result?.statement_id) return;

    // Validate inputs inline
    setOpeningBalanceError(null);
    setClosingBalanceError(null);

    const openingPaise = parseRupeesToPaise(openingBalanceInput);
    const closingPaise = parseRupeesToPaise(closingBalanceInput);

    let hasError = false;

    if (openingPaise === null) {
      setOpeningBalanceError('Please enter a valid amount (e.g., 1000.50)');
      hasError = true;
    }

    if (closingPaise === null) {
      setClosingBalanceError('Please enter a valid amount (e.g., 1000.50)');
      hasError = true;
    }

    if (hasError) return;

    setIsSavingBalances(true);
    setBalanceSaveSuccess(false);

    try {
      const response = await setImportBalances(
        result.statement_id,
        openingPaise!,
        closingPaise!,
        member
      );

      if (response.success) {
        setBalanceSaveSuccess(true);

        // Refresh the import status to get updated state
        const updated = await fetchV2Import(result.statement_id);
        setResult({
          ...result,
          status: updated.status,
          delta_paise: updated.delta_paise ?? response.delta_paise,
          validation: {
            ...result.validation,
            valid: response.valid,
            opening_balance_paise: openingPaise!,
            closing_balance_paise: closingPaise!,
          },
          committed: response.committed ? {
            inserted: response.inserted,
            skipped: response.skipped,
          } : undefined,
        });
      } else {
        setError(response.error || 'Failed to save balances');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save balances');
    } finally {
      setIsSavingBalances(false);
    }
  }, [result, member, openingBalanceInput, closingBalanceInput]);

  // Handle bbox drawn by user
  const handleBboxDrawn = useCallback((bboxNorm: number[]) => {
    setDrawnBboxNorm(bboxNorm);
  }, []);

  // Handle re-extract with bbox
  const handleReextract = useCallback(async () => {
    if (!result?.statement_id || !drawnBboxNorm || drawnBboxNorm.length < 4) return;

    setIsReextracting(true);
    setError(null);

    try {
      const response = await reextractWithBbox(
        result.statement_id,
        [
          {
            page_number: 1,
            x0: drawnBboxNorm[0]!,
            y0: drawnBboxNorm[1]!,
            x1: drawnBboxNorm[2]!,
            y1: drawnBboxNorm[3]!,
          },
        ],
        applyToAllPages,
        true // save_as_template
      );

      if (response.success) {
        // Update result with new extraction data
        setResult(response);
        // Exit drawing mode
        setIsDrawingMode(false);
        // Clear drawn bbox (it will be shown as the suggested bbox now)
        setDrawnBboxNorm(null);
      } else {
        setError(response.error || 'Re-extraction failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Re-extraction failed');
    } finally {
      setIsReextracting(false);
    }
  }, [result, drawnBboxNorm, applyToAllPages]);

  // Uploading phase
  if (phase === 'uploading') {
    return (
      <Card>
        <CardContent className="p-8">
          <div className="flex flex-col items-center gap-6">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
            <div className="space-y-2 text-center">
              <p className="font-medium text-lg">Uploading and processing PDF...</p>
              <p className="text-sm text-muted-foreground">
                {file.name} • {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <div className="w-full max-w-md space-y-2">
              <Progress value={Math.min(progress, 100)} className="h-2" />
              <p className="text-xs text-center text-muted-foreground">
                Extracting transactions and validating balances...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error phase
  if (phase === 'error' || (result?.status === 'FAILED')) {
    return (
      <Card>
        <CardContent className="p-8">
          <div className="flex flex-col items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
              <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-2xl font-bold">Import Failed</h2>
            <Alert variant="destructive" className="max-w-md">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error || result?.error || 'Unknown error occurred'}</AlertDescription>
            </Alert>
            <div className="flex gap-4 mt-4">
              <Button variant="outline" onClick={onReset}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Try Again
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Preview phase - show PDF preview with overlay and preview rows
  if (phase === 'preview' && result) {
    const hasPreviewRows = result.preview_rows && result.preview_rows.length > 0;

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Eye className="h-6 w-6 text-primary" />
              Preview Import
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Review the extracted transactions and suggested bounding box
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={result.validation.valid ? 'default' : 'secondary'}>
              {result.validation.valid ? 'Valid' : 'Needs Review'}
            </Badge>
          </div>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: PDF Preview */}
          <PdfPreviewWithOverlay
            file={file}
            suggestedBboxNorm={result.suggested_bbox_norm}
            isDrawing={isDrawingMode}
            onBboxDrawn={handleBboxDrawn}
            drawnBboxNorm={drawnBboxNorm}
            applyToAllPages={applyToAllPages}
          />

          {/* Right: Preview Rows & Validation */}
          <div className="space-y-6">
            {/* BBox Drawing Controls */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Table Region Selection</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {!isDrawingMode ? (
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      If the extraction missed transactions or used the wrong area, you can draw the table region manually.
                    </p>
                    <Button
                      variant="outline"
                      onClick={() => setIsDrawingMode(true)}
                      className="w-full"
                    >
                      <Pencil className="mr-2 h-4 w-4" />
                      Draw table region
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      Drag to draw a rectangle around the transaction table on page 1.
                    </p>

                    {/* Apply to all pages checkbox */}
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="apply-to-all"
                        checked={applyToAllPages}
                        onCheckedChange={(checked) => setApplyToAllPages(checked as boolean)}
                      />
                      <Label htmlFor="apply-to-all" className="text-sm font-normal cursor-pointer">
                        Apply to all pages
                      </Label>
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setIsDrawingMode(false);
                          setDrawnBboxNorm(null);
                        }}
                        className="flex-1"
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleReextract}
                        disabled={!drawnBboxNorm || isReextracting}
                        className="flex-1"
                      >
                        {isReextracting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Re-extracting...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Re-extract with BBox
                          </>
                        )}
                      </Button>
                    </div>

                    {drawnBboxNorm && (
                      <p className="text-xs text-green-600">
                        ✓ Region selected. Click &quot;Re-extract with BBox&quot; to apply.
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Validation Summary */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Validation Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Bank</p>
                    <p className="font-medium">{result.bank}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Transactions</p>
                    <p className="font-medium">{result.transaction_count}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Extractor</p>
                    <p className="font-medium capitalize">{result.extractor}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Template Applied</p>
                    <p className="font-medium">{result.template_applied ? 'Yes' : 'No'}</p>
                  </div>
                </div>

                <div className="border-t pt-3 mt-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Opening Balance</p>
                      <p className="font-medium">{formatPaise(result.validation.opening_balance_paise)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Closing Balance</p>
                      <p className="font-medium">{formatPaise(result.validation.closing_balance_paise)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Delta</p>
                      <p className={cn('font-medium',
                        result.delta_paise === null ? 'text-muted-foreground' :
                        result.delta_paise !== 0 ? 'text-amber-600' : 'text-green-600'
                      )}>
                        {result.delta_paise === null ? '—' : formatPaise(result.delta_paise)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Status</p>
                      <p className={cn('font-medium', result.validation.valid ? 'text-green-600' : 'text-amber-600')}>
                        {result.validation.valid ? 'Valid' : 'Needs Attention'}
                      </p>
                    </div>
                  </div>
                  {result.validation.reason && (
                    <p className="text-sm text-muted-foreground mt-2">{result.validation.reason}</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Preview Rows Table */}
            {hasPreviewRows && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">
                    Preview Rows (First {result.preview_rows!.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="text-xs">Date</TableHead>
                          <TableHead className="text-xs">Description</TableHead>
                          <TableHead className="text-xs text-right">Debit</TableHead>
                          <TableHead className="text-xs text-right">Credit</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {result.preview_rows!.map((row, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="text-xs py-2">{row.date}</TableCell>
                            <TableCell className="text-xs py-2 max-w-[200px] truncate" title={row.description}>
                              {row.description}
                            </TableCell>
                            <TableCell className="text-xs py-2 text-right">
                              {row.debit_paise ? formatPaise(row.debit_paise) : '—'}
                            </TableCell>
                            <TableCell className="text-xs py-2 text-right">
                              {row.credit_paise ? formatPaise(row.credit_paise) : '—'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={onReset}>
            Cancel
          </Button>
          <Button onClick={() => { setPhase('completed'); onComplete?.(); }}>
            Continue
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    );
  }

  // Completed phase - show result based on status
  if (phase === 'completed' && result) {
    const statusConfigItem = statusConfig[result.status];
    const StatusIcon = statusConfigItem.icon;
    const showBalanceInputs = needsBalanceInput(result);

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <StatusIcon className={cn('h-5 w-5', statusConfigItem.color)} />
            Import {statusConfigItem.label}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Status Badge */}
          <div className="flex items-center gap-2">
            <Badge variant={statusConfigItem.variant}>{statusConfigItem.label}</Badge>
            <span className="text-sm text-muted-foreground">Statement ID: {result.statement_id}</span>
          </div>

          {/* File Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">File</p>
              <p className="font-medium truncate">{result.filename}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Bank</p>
              <p className="font-medium">{result.bank}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Transactions</p>
              <p className="font-medium">{result.transaction_count}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Extractor</p>
              <p className="font-medium capitalize">{result.extractor}</p>
            </div>
          </div>

          {/* Validation Info */}
          <div className="rounded-lg border p-4 space-y-2">
            <p className="font-medium">Validation Results</p>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Opening Balance</p>
                <p className="font-medium">{formatPaise(result.validation.opening_balance_paise)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Closing Balance</p>
                <p className="font-medium">{formatPaise(result.validation.closing_balance_paise)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Delta (Discrepancy)</p>
                <p className={cn('font-medium',
                  result.delta_paise === null ? 'text-muted-foreground' :
                  result.delta_paise !== 0 ? 'text-amber-600' : 'text-green-600'
                )}>
                  {result.delta_paise === null ? '—' : formatPaise(result.delta_paise)}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p className={cn('font-medium', result.validation.valid ? 'text-green-600' : 'text-amber-600')}>
                  {result.validation.valid ? 'Valid' : 'Needs Attention'}
                </p>
              </div>
            </div>
            {result.validation.reason && (
              <p className="text-sm text-muted-foreground mt-2">{result.validation.reason}</p>
            )}
          </div>

          {/* Balance Input Form - Show when balances are missing */}
          {showBalanceInputs && (
            <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10 p-4 space-y-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <p className="font-medium text-amber-900 dark:text-amber-100">Missing Balance Information</p>
              </div>
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Please enter the opening and closing balances from your statement to validate the import.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="opening-balance" className="text-amber-900 dark:text-amber-100">
                    Opening Balance (₹)
                  </Label>
                  <Input
                    id="opening-balance"
                    type="text"
                    inputMode="decimal"
                    placeholder="e.g., 1000.50"
                    value={openingBalanceInput}
                    onChange={(e) => {
                      setOpeningBalanceInput(e.target.value);
                      setOpeningBalanceError(null);
                    }}
                    className={cn(
                      'bg-white dark:bg-background',
                      openingBalanceError && 'border-red-500 focus-visible:ring-red-500'
                    )}
                  />
                  {openingBalanceError && (
                    <p className="text-xs text-red-600">{openingBalanceError}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="closing-balance" className="text-amber-900 dark:text-amber-100">
                    Closing Balance (₹)
                  </Label>
                  <Input
                    id="closing-balance"
                    type="text"
                    inputMode="decimal"
                    placeholder="e.g., 2000.75"
                    value={closingBalanceInput}
                    onChange={(e) => {
                      setClosingBalanceInput(e.target.value);
                      setClosingBalanceError(null);
                    }}
                    className={cn(
                      'bg-white dark:bg-background',
                      closingBalanceError && 'border-red-500 focus-visible:ring-red-500'
                    )}
                  />
                  {closingBalanceError && (
                    <p className="text-xs text-red-600">{closingBalanceError}</p>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-3 pt-2">
                <Button
                  onClick={handleSaveBalances}
                  disabled={isSavingBalances}
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                >
                  {isSavingBalances ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save Balances & Validate
                    </>
                  )}
                </Button>

                <Button
                  variant="outline"
                  onClick={handleRefresh}
                  disabled={isSavingBalances}
                >
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Refresh Status
                </Button>
              </div>

              {balanceSaveSuccess && (
                <Alert className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 mt-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800 dark:text-green-200">
                    Balances saved successfully. {result.status === 'COMMITTED' ? 'Import committed!' : 'Validation updated.'}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          {/* Status-specific Alerts */}
          {result.status === 'COMMITTED' && (
            <Alert className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertTitle>Successfully Committed</AlertTitle>
              <AlertDescription>
                {result.committed
                  ? `${result.committed.inserted} transactions inserted, ${result.committed.skipped} skipped`
                  : `${result.transaction_count} transactions committed to ledger`}
              </AlertDescription>
            </Alert>
          )}

          {result.status === 'NEEDS_REVIEW' && !showBalanceInputs && (
            <Alert variant="destructive" className="border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertTitle>Validation Failed</AlertTitle>
              <AlertDescription>
                Balance discrepancy detected ({result.delta_paise === null ? '—' : formatPaise(result.delta_paise)}).
                Please review and resolve in quarantine.
              </AlertDescription>
            </Alert>
          )}

          {result.status === 'STAGED' && (
            <Alert>
              <FileText className="h-4 w-4" />
              <AlertTitle>Ready to Commit</AlertTitle>
              <AlertDescription>
                Import is staged and ready to be committed to the ledger.
              </AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            {result.status === 'COMMITTED' && (
              <>
                <Link href="/transactions">
                  <Button>View Transactions</Button>
                </Link>
                <Button variant="outline" onClick={onReset}>
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Import Another
                </Button>
              </>
            )}

            {result.status === 'NEEDS_REVIEW' && !showBalanceInputs && (
              <>
                <Link href="/quarantine">
                  <Button variant="destructive">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Resolve in Quarantine
                  </Button>
                </Link>
                <Button variant="outline" onClick={handleRefresh} disabled={isCommitting}>
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Refresh Status
                </Button>
                <Button variant="ghost" onClick={onReset}>
                  Cancel
                </Button>
              </>
            )}

            {result.status === 'STAGED' && (
              <>
                <Button
                  onClick={handleCommit}
                  disabled={isCommitting || !result.validation.valid}
                  title={!result.validation.valid ? 'Cannot commit: validation failed' : undefined}
                >
                  {isCommitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Committing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Commit to Ledger
                    </>
                  )}
                </Button>
                <Button variant="outline" onClick={handleDiscard} disabled={isDiscarding}>
                  {isDiscarding ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Discarding...
                    </>
                  ) : (
                    <>
                      <Trash2 className="mr-2 h-4 w-4" />
                      Discard
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
}
