'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileSpreadsheet, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface UploadDropzoneCardProps {
  onDrop: (acceptedFiles: File[]) => void;
  loading?: boolean;
  disabled?: boolean;
}

export function UploadDropzoneCard({ onDrop, loading = false, disabled = false }: UploadDropzoneCardProps) {
  const handleDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (!loading && !disabled) {
        onDrop(acceptedFiles);
      }
    },
    [onDrop, loading, disabled]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: loading || disabled,
  });

  return (
    <Card>
      <CardContent className="p-8">
        <div
          {...getRootProps()}
          className={cn(
            'flex flex-col items-center justify-center gap-4 text-center cursor-pointer border-2 border-dashed rounded-lg p-12 transition-colors',
            isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50',
            (loading || disabled) && 'pointer-events-none opacity-50'
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
                    : 'Drag and drop your bank statements here'}
                </p>
                <p className="text-sm text-muted-foreground">
                  Support for CSV, Excel, and PDF bank statements
                </p>
                <p className="text-xs text-muted-foreground">
                  Supported formats: .csv, .xlsx, .xls, .pdf
                </p>
              </div>
              <Button variant="outline" type="button">
                <Upload className="h-4 w-4 mr-2" />
                Select File
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
