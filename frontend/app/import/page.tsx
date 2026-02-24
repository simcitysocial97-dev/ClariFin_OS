'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { detectImportColumns, executeImport, type ImportDetectResult, type ImportMapping, type ImportExecuteResult } from '@/lib/api/client';
import { ColumnMapper } from '@/components/import/ColumnMapper';
import { ImportPreview } from '@/components/import/ImportPreview';
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle, ArrowLeft, ArrowRight, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

type Step = 'upload' | 'map' | 'preview' | 'done';

const STEPS = [
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'map', label: 'Map Columns', icon: FileSpreadsheet },
  { id: 'preview', label: 'Preview', icon: CheckCircle },
  { id: 'done', label: 'Done', icon: CheckCircle },
];

export default function ImportPage() {
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [detectResult, setDetectResult] = useState<ImportDetectResult | null>(null);
  const [mapping, setMapping] = useState<ImportMapping | null>(null);
  const [executeResult, setExecuteResult] = useState<ImportExecuteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const uploadedFile = acceptedFiles[0];
    
    // Validate file type
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ];
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const hasValidExtension = validExtensions.some((ext) => 
      uploadedFile.name.toLowerCase().endsWith(ext)
    );
    
    if (!validTypes.includes(uploadedFile.type) && !hasValidExtension) {
      toast({
        title: 'Invalid file type',
        description: 'Please upload a CSV or Excel file (.csv, .xlsx, .xls)',
        variant: 'destructive',
      });
      return;
    }

    setFile(uploadedFile);
    setLoading(true);
    setError(null);

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
  }, [toast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
    disabled: loading,
  });

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
    if (currentStep === 'map') {
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

  const currentStepIndex = STEPS.findIndex((s) => s.id === currentStep);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Import Transactions</h1>
        <p className="text-muted-foreground mt-1">
          Import transactions from CSV or Excel files
        </p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center justify-center gap-2">
        {STEPS.map((step, index) => {
          const StepIcon = step.icon;
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
              {index < STEPS.length - 1 && (
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

      {/* Content */}
      <div className="max-w-4xl mx-auto">
        {/* Step 1: Upload */}
        {currentStep === 'upload' && (
          <Card>
            <CardContent className="p-8">
              <div
                {...getRootProps()}
                className={cn(
                  'flex flex-col items-center justify-center gap-4 text-center cursor-pointer border-2 border-dashed rounded-lg p-12 transition-colors',
                  isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50',
                  loading && 'pointer-events-none opacity-50'
                )}
              >
                <input {...getInputProps()} />
                
                {loading ? (
                  <>
                    <Loader2 className="h-12 w-12 text-primary animate-spin" />
                    <div className="space-y-2">
                      <p className="font-medium">Analyzing file...</p>
                      <p className="text-sm text-muted-foreground">
                        Detecting columns and data types
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                      <FileSpreadsheet className="h-8 w-8 text-primary" />
                    </div>
                    <div className="space-y-2">
                      <p className="text-lg font-medium">
                        {isDragActive
                          ? 'Drop your file here'
                          : 'Upload CSV or Excel file'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Drag and drop a file, or click to browse
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Supported formats: .csv, .xlsx, .xls
                      </p>
                    </div>
                    <Button variant="outline">
                      Select File
                    </Button>
                  </>
                )}
              </div>

              {error && (
                <Alert variant="destructive" className="mt-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
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

            <ColumnMapper
              detectResult={detectResult}
              onMappingChange={handleMappingChange}
            />

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

            <ImportPreview detectResult={detectResult} mapping={mapping} />

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
    </div>
  );
}