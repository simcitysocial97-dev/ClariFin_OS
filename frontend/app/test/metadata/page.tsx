'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { parseStatement } from '@/lib/parser';

interface TestResult {
  fileName: string;
  passed: boolean;
  metadata: {
    bankName?: string;
    cardNumber?: string;
    totalAmountDue?: number;
    minimumAmountDue?: number;
    creditLimit?: number;
    dueDate?: string;
    openingBalance?: number;
    billCycleStart?: string;
    billCycleEnd?: string;
  };
  validation: {
    isValid: boolean;
    message: string;
    calculatedTotal: number;
    expectedTotal: number;
    bankTotal: number;
    difference: number;
    totalDebits: number;
    totalCredits: number;
    transactionCount: number;
  };
  errors: string[];
}

export default function MetadataTestPage() {
  const [results, setResults] = useState<TestResult[]>([]);
  const [isTesting, setIsTesting] = useState(false);
  const [progress, setProgress] = useState(0);
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsTesting(true);
    setProgress(0);
    const newResults: TestResult[] = [];

    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      setProgress(((i + 1) / acceptedFiles.length) * 100);

      try {
        const result = await parseStatement(file);

        const testResult: TestResult = {
          fileName: file.name,
          passed: result.validation.isValid,
          metadata: result.metadata,
          validation: result.validation,
          errors: result.validation.isValid ? [] : [result.validation.message]
        };

        newResults.push(testResult);
      } catch (error) {
        newResults.push({
          fileName: file.name,
          passed: false,
          metadata: {},
          validation: {
            isValid: false,
            message: (error as Error).message,
            calculatedTotal: 0,
            expectedTotal: 0,
            bankTotal: 0,
            difference: 0,
            totalDebits: 0,
            totalCredits: 0,
            transactionCount: 0
          },
          errors: [(error as Error).message]
        });
      }
    }

    setResults(newResults);
    setIsTesting(false);
    setProgress(100);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Metadata Extractor Test</h1>
          <p className="text-muted-foreground mt-1">
            Test metadata extraction against uploaded PDF statements
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          Browser Parser v2.0
        </Badge>
      </div>

      {/* Upload Zone */}
      <Card>
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            {isDragActive ? (
              <p className="text-lg font-medium">Drop PDF files here...</p>
            ) : (
              <>
                <p className="text-lg font-medium">Drag & drop PDF files here</p>
                <p className="text-sm text-muted-foreground mt-1">
                  or click to select files
                </p>
              </>
            )}
          </div>

          {isTesting && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Testing files...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Test Results</h2>
            <div className="flex gap-2">
              <Badge variant="default" className="bg-green-500">
                {results.filter(r => r.passed).length} Passed
              </Badge>
              <Badge variant="destructive">
                {results.filter(r => !r.passed).length} Failed
              </Badge>
            </div>
          </div>

          {results.map((result, index) => (
            <Card key={index} className={result.passed ? 'border-green-200' : 'border-red-200'}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <CardTitle className="text-base font-medium">{result.fileName}</CardTitle>
                  </div>
                  {result.passed ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Bank</p>
                    <p className="font-medium">{result.metadata.bankName || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Card Number</p>
                    <p className="font-medium">{result.metadata.cardNumber || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Total Due</p>
                    <p className="font-medium">₹{result.metadata.totalAmountDue?.toLocaleString('en-IN') || '0'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Min Due</p>
                    <p className="font-medium">₹{result.metadata.minimumAmountDue?.toLocaleString('en-IN') || '0'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Credit Limit</p>
                    <p className="font-medium">₹{result.metadata.creditLimit?.toLocaleString('en-IN') || '0'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Opening Balance</p>
                    <p className="font-medium">₹{result.metadata.openingBalance?.toLocaleString('en-IN') || '0'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Due Date</p>
                    <p className="font-medium">{result.metadata.dueDate || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Bill Cycle</p>
                    <p className="font-medium">
                      {result.metadata.billCycleStart && result.metadata.billCycleEnd
                        ? `${result.metadata.billCycleStart} - ${result.metadata.billCycleEnd}`
                        : 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Validation Status */}
                <div className={`mt-4 p-3 rounded-lg text-sm ${
                  result.validation.isValid ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                }`}>
                  <div className="flex items-center gap-2">
                    {result.validation.isValid ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <AlertCircle className="h-4 w-4" />
                    )}
                    <span className="font-medium">{result.validation.message}</span>
                  </div>
                  {!result.validation.isValid && (
                    <div className="mt-2 text-xs space-y-1">
                      <p>Calculated: ₹{result.validation.calculatedTotal}</p>
                      <p>Expected: ₹{result.validation.expectedTotal}</p>
                      <p>Difference: ₹{result.validation.difference}</p>
                    </div>
                  )}
                </div>

                {/* Errors */}
                {result.errors.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {result.errors.map((error, i) => (
                      <p key={i} className="text-sm text-red-600 flex items-center gap-2">
                        <XCircle className="h-3 w-3" />
                        {error}
                      </p>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Instructions */}
      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-sm font-medium">How to Use</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>1. Drag and drop PDF bank statements into the upload zone above</p>
          <p>2. The browser parser will extract metadata from each PDF</p>
          <p>3. Results show extracted metadata and validation status</p>
          <p>4. Validation compares calculated total vs stated total from the statement</p>
          <p>5. All processing happens in the browser - no files are uploaded to any server</p>
        </CardContent>
      </Card>
    </div>
  );
}