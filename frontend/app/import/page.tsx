'use client';

import { Suspense, useState, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { CheckCircle, AlertCircle, ArrowLeft, ArrowRight, Loader2, Upload, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { ErrorBoundary } from '@/components/error-boundary';
import { detectImportColumns, executeImport, type ImportDetectResult, type ImportMapping, type ImportExecuteResult } from '@/lib/api/client';
import { ColumnMapper } from '@/components/import/ColumnMapper';
import { ImportPreview } from '@/components/import/ImportPreview';
import { UploadDropzoneCard } from '@/components/import/upload-dropzone-card';
import { ImportHistoryList } from '@/components/import/import-history-list';
import { V2ImportStatus } from '@/components/import/v2-import-status';

type Step = 'upload' | 'map' | 'preview' | 'done' | 'v2-import';

const STEPS = [
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'map', label: 'Map Columns', icon: Upload },
  { id: 'preview', label: 'Preview', icon: CheckCircle },
  { id: 'done', label: 'Done', icon: CheckCircle },
];

const V2_STEPS = [
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'v2-import', label: 'Processing', icon: Sparkles },
  { id: 'done', label: 'Done', icon: CheckCircle },
];

// Widget Error Fallback
function WidgetErrorFallback() {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Component Error</AlertTitle>
      <AlertDescription>
        Failed to load import component. Please try refreshing.
      </AlertDescription>
    </Alert>
  );
}

function ImportContent() {
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [detectResult, setDetectResult] = useState<ImportDetectResult | null>(null);
  const [mapping, setMapping] = useState<ImportMapping | null>(null);
  const [executeResult, setExecuteResult] = useState<ImportExecuteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useV2Import, setUseV2Import] = useState(false);

  const isPdfFile = (f: File | null): boolean => {
    if (!f) return false;
    return f.name.toLowerCase().endsWith('.pdf');
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const uploadedFile = acceptedFiles[0];
    if (!uploadedFile) return;
    
    // Validate file type
    const validExtensions = ['.csv', '.xlsx', '.xls', '.pdf'];
    const hasValidExtension = validExtensions.some((ext) => 
      uploadedFile.name.toLowerCase().endsWith(ext)
    );
    
    if (!hasValidExtension) {
      toast({
        title: 'Invalid file type',
        description: 'Please upload a CSV, Excel, or PDF file',
        variant: 'destructive',
      });
      return;
    }

    setFile(uploadedFile);
    setError(null);

    // Route to V2 import for PDFs when toggle is enabled
    if (useV2Import && isPdfFile(uploadedFile)) {
      setCurrentStep('v2-import');
      return;
    }

    // Legacy flow for CSV/Excel
    setLoading(true);

    try {
      const result = await detectImportColumns(uploadedFile);
      setDetectResult(result);
      setCurrentStep('map');
      toast({
        title: 'File analyzed',
        description: `Detected ${result.columns.length} columns and ${result.row_count} rows`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze file');
      toast({
        title: 'Analysis failed',
        description: err instanceof Error ? err.message : 'Failed to analyze file',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast, useV2Import]);

  const handleMappingChange = useCallback((newMapping: ImportMapping) => {
    setMapping(newMapping);
  }, []);

  const handleNext = () => {
    if (currentStep === 'map') {
      if (!mapping?.date_column || !mapping?.description_column || !mapping?.amount_column) {
        toast({
          title: 'Required fields missing',
          description: 'Please select Date, Description, and Amount columns',
          variant: 'destructive',
        });
        return;
      }
      setCurrentStep('preview');
    }
  };

  const handleBack = () => {
    if (currentStep === 'map' || currentStep === 'v2-import') {
      setCurrentStep('upload');
      setFile(null);
      setDetectResult(null);
      setMapping(null);
    } else if (currentStep === 'preview') {
      setCurrentStep('map');
    } else if (currentStep === 'done') {
      setCurrentStep('upload');
      setFile(null);
      setDetectResult(null);
      setMapping(null);
      setExecuteResult(null);
    }
  };

  const handleExecute = async () => {
    if (!file || !mapping) return;

    setLoading(true);
    setError(null);

    try {
      const result = await executeImport(file.name, mapping);
      setExecuteResult(result);
      setCurrentStep('done');
      
      if (result.success) {
        toast({
          title: 'Import successful',
          description: `Imported ${result.imported} transactions`,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import');
      toast({
        title: 'Import failed',
        description: err instanceof Error ? err.message : 'Failed to import',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCurrentStep('upload');
    setFile(null);
    setDetectResult(null);
    setMapping(null);
    setExecuteResult(null);
    setError(null);
  };

  const handleV2Complete = () => {
    toast({
      title: 'V2 Import complete',
      description: 'Your PDF has been processed',
    });
  };

  // Determine which steps to show based on flow type
  const activeSteps = (useV2Import && file && isPdfFile(file)) ? V2_STEPS : STEPS;
  const currentStepIndex = activeSteps.findIndex((s) => s.id === currentStep);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Import Transactions</h1>
          <p className="text-muted-foreground mt-1">
            Import transactions from CSV, Excel, or PDF bank statements
          </p>
        </div>
        {/* V2 Import Toggle */}
        <div className="flex items-center gap-3 bg-muted/50 rounded-lg px-4 py-2">
          <div className="flex flex-col">
            <Label htmlFor="v2-toggle" className="text-sm font-medium cursor-pointer flex items-center gap-1">
              <Sparkles className="h-3.5 w-3.5 text-amber-500" />
              Use V2 Import
            </Label>
            <span className="text-xs text-muted-foreground">
              For PDFs with staging & validation
            </span>
          </div>
          <Switch
            id="v2-toggle"
            checked={useV2Import}
            onCheckedChange={setUseV2Import}
          />
        </div>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center justify-center gap-2">
        {activeSteps.map((step, index) => {
          const isActive = index === currentStepIndex;
          const isCompleted = index < currentStepIndex;
          
          return (
            <div key={step.id} className="flex items-center">
              <div
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-full transition-colors',
                  isActive && 'bg-primary text-primary-foreground',
                  isCompleted && 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
                  !isActive && !isCompleted && 'bg-muted text-muted-foreground'
                )}
              >
                <div
                  className={cn(
                    'flex items-center justify-center h-6 w-6 rounded-full text-sm font-medium',
                    isActive && 'bg-primary-foreground/20',
                    isCompleted && 'bg-green-200 dark:bg-green-800'
                  )}
                >
                  {isCompleted ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    index + 1
                  )}
                </div>
                <span className="hidden sm:inline">{step.label}</span>
              </div>
              {index < activeSteps.length - 1 && (
                <div
                  className={cn(
                    'w-8 h-0.5 mx-1',
                    index < currentStepIndex ? 'bg-green-500' : 'bg-muted'
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Main Import Flow */}
        <div className="lg:col-span-2 space-y-6">
          {/* Step 1: Upload */}
          {currentStep === 'upload' && (
            <ErrorBoundary fallback={<WidgetErrorFallback />}>
              <Suspense fallback={<Skeleton className="h-[300px]" />}>
                <UploadDropzoneCard onDrop={onDrop} loading={loading} />
                
                {error && (
                  <Alert variant="destructive" className="mt-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </Suspense>
            </ErrorBoundary>
          )}

          {/* Step 2: Column Mapping */}
          {currentStep === 'map' && detectResult && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{file?.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {detectResult.row_count} rows detected
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={handleBack}>
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
              </div>

              <ErrorBoundary fallback={<WidgetErrorFallback />}>
                <Suspense fallback={<Skeleton className="h-[400px]" />}>
                  <ColumnMapper
                    detectResult={detectResult}
                    onMappingChange={handleMappingChange}
                  />
                </Suspense>
              </ErrorBoundary>

              <div className="flex justify-end">
                <Button onClick={handleNext}>
                  Continue to Preview
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Preview */}
          {currentStep === 'preview' && detectResult && mapping && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Preview Import</p>
                  <p className="text-sm text-muted-foreground">
                    Review before importing
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={handleBack}>
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Mapping
                </Button>
              </div>

              <ErrorBoundary fallback={<WidgetErrorFallback />}>
                <Suspense fallback={<Skeleton className="h-[400px]" />}>
                  <ImportPreview detectResult={detectResult} mapping={mapping} />
                </Suspense>
              </ErrorBoundary>

              <div className="flex justify-between">
                <Button variant="outline" onClick={handleBack}>
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
                <Button onClick={handleExecute} disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Importing...
                    </>
                  ) : (
                    <>
                      Import {detectResult.row_count} Transactions
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* V2 Import Step */}
          {currentStep === 'v2-import' && file && (
            <ErrorBoundary fallback={<WidgetErrorFallback />}>
              <Suspense fallback={<Skeleton className="h-[400px]" />}>
                <V2ImportStatus
                  file={file}
                  member="Self"
                  autoCommit={true}
                  onComplete={handleV2Complete}
                  onReset={handleReset}
                />
              </Suspense>
            </ErrorBoundary>
          )}

          {/* Step 4: Done */}
          {currentStep === 'done' && executeResult && (
            <Card>
              <CardContent className="p-8 text-center">
                {executeResult.success ? (
                  <>
                    <div className="h-16 w-16 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mx-auto mb-4">
                      <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Import Complete!</h2>
                    <p className="text-muted-foreground mb-6">
                      Successfully imported {executeResult.imported} transactions
                      {executeResult.skipped > 0 && ` (${executeResult.skipped} skipped)`}
                    </p>
                    
                    <div className="flex justify-center gap-4">
                      <Link href="/transactions">
                        <Button>
                          View Transactions
                        </Button>
                      </Link>
                      <Button variant="outline" onClick={handleReset}>
                        Import Another
                      </Button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="h-16 w-16 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center mx-auto mb-4">
                      <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Import Failed</h2>
                    <p className="text-muted-foreground mb-2">
                      {executeResult.imported} transactions imported before failure
                    </p>
                    {executeResult.errors.length > 0 && (
                      <div className="text-left bg-muted rounded-lg p-4 mb-6 max-h-32 overflow-y-auto">
                        {executeResult.errors.map((err, i) => (
                          <p key={i} className="text-sm text-destructive">{err}</p>
                        ))}
                      </div>
                    )}
                    
                    <div className="flex justify-center gap-4">
                      <Button variant="outline" onClick={handleReset}>
                        Try Again
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Import History */}
        <div className="space-y-6">
          {/* Import History */}
          <ErrorBoundary fallback={<WidgetErrorFallback />}>
            <Suspense fallback={<Skeleton className="h-[300px]" />}>
              <ImportHistoryList />
            </Suspense>
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}

export default function ImportPage() {
  return (
    <div className="space-y-6 p-6">
      <ErrorBoundary fallback={
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Page Error</AlertTitle>
          <AlertDescription>
            Failed to load import page. Please try refreshing.
          </AlertDescription>
        </Alert>
      }>
        <Suspense fallback={
          <div className="space-y-6">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-[400px]" />
          </div>
        }>
          <ImportContent />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}
