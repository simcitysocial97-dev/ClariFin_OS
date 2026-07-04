'use client';

import { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { Upload, FileText, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUpload, useOverview, useStatements, useTransactions } from '@/lib/hooks/use-finance-data';
import { useMember } from '@/lib/context/member-context';

interface UploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadModal({ open, onOpenChange }: UploadModalProps) {
  const { member: contextMember } = useMember();
  const selectedMember = contextMember === 'All' ? 'Self' : contextMember;
  const [processingLog, setProcessingLog] = useState<string[]>([]);
  const [uploadResult, setUploadResult] = useState<{
    bank: string;
    transactionCount: number;
    validationStatus: string;
  } | null>(null);
  
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [parsedFiles, setParsedFiles] = useState(0);
  
  const { toast } = useToast();
  const { upload, result: serverResult, error: serverError } = useUpload();
  const { refetch: refetchOverview } = useOverview();
  const { refetch: refetchStatements } = useStatements();
  const { refetch: refetchTransactions } = useTransactions();

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!open) {
      setProcessingLog([]);
      setUploadResult(null);
      setProgress(0);
      setParsedFiles(0);
      setTotalFiles(0);
      setIsUploading(false);
    }
  }, [open]);

  // Handle server upload result
  useEffect(() => {
    if (serverResult && isUploading) {
      setProcessingLog(serverResult.log || []);
      setUploadResult({
        bank: serverResult.bank,
        transactionCount: serverResult.transaction_count,
        validationStatus: serverResult.validation_status,
      });
      setProgress(100);
      
      // Show success toast
      toast({
        title: 'Upload successful!',
        description: `Extracted ${serverResult.transaction_count} transactions from ${serverResult.bank}. Validation: ${serverResult.validation_status}`,
      });
      
      // Refetch all data
      refetchOverview();
      refetchStatements();
      refetchTransactions();
      
      // Close modal after delay
      setTimeout(() => {
        setIsUploading(false);
        onOpenChange(false);
      }, 2000);
    }
  }, [serverResult, isUploading, toast, refetchOverview, refetchStatements, refetchTransactions, onOpenChange]);

  // Handle server upload error
  useEffect(() => {
    if (serverError && isUploading) {
      toast({
        title: 'Upload failed',
        description: serverError.message,
        variant: 'destructive',
      });
      setIsUploading(false);
    }
  }, [serverError, isUploading, toast]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      // Validate all files are PDFs
      const invalidFiles = acceptedFiles.filter(
        (file) => file.type !== 'application/pdf'
      );
      if (invalidFiles.length > 0) {
        toast({
          title: 'Invalid file type',
          description: `${invalidFiles.length} file(s) are not PDFs`,
          variant: 'destructive',
        });
        return;
      }

      setIsUploading(true);
      setProgress(0);
      setTotalFiles(acceptedFiles.length);
      setParsedFiles(0);
      setProcessingLog([]);
      setUploadResult(null);

      // Server-side upload - process files one by one
      for (let i = 0; i < acceptedFiles.length; i++) {
        const file = acceptedFiles[i];
        setProgress(Math.round((i / acceptedFiles.length) * 50)); // First 50% for upload
        
        try {
          if (!file) return;
          await upload(file, selectedMember);
          setParsedFiles((prev) => prev + 1);
        } catch (error) {
          // Error handled by useEffect
          setParsedFiles((prev) => prev + 1);
        }
      }
    },
    [toast, selectedMember, upload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 10,
    disabled: isUploading,
    multiple: true,
  });

  // Get badge color for validation status
  const getValidationBadgeColor = (status: string) => {
    switch (status) {
      case 'exact_match':
        return 'bg-green-500';
      case 'close_match':
        return 'bg-amber-500';
      case 'mismatch':
        return 'bg-red-500';
      case 'emi_exception':
        return 'bg-blue-500';
      case 'credit_balance':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload Bank Statements</DialogTitle>
        </DialogHeader>
        
        {/* Member Selector - shows current context member */}
        {!isUploading && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Member:</span>
            <span className="text-sm font-medium">{selectedMember}</span>
            <span className="text-xs text-muted-foreground">(Change in sidebar)</span>
          </div>
        )}
        
        <div
          {...getRootProps()}
          className={cn(
            'flex flex-col items-center justify-center gap-4 text-center cursor-pointer border-2 border-dashed rounded-lg p-8 transition-colors',
            isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50',
            isUploading && 'pointer-events-none opacity-50'
          )}
        >
          <input {...getInputProps()} />

          {isUploading ? (
            <>
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
                <FileText className="h-6 w-6 text-primary" />
              </div>
              <div className="space-y-2 w-full max-w-xs">
                <p className="text-sm font-medium">
                  Processing on server... ({parsedFiles}/{totalFiles})
                </p>
                <Progress value={progress} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  {progress === 100
                    ? 'Complete!'
                    : 'Processing files...'}
                </p>
              </div>
            </>
          ) : (
            <>
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Upload className="h-6 w-6 text-primary" />
              </div>
              <div className="space-y-2">
                <p className="font-medium">
                  {isDragActive
                    ? 'Drop your PDFs here'
                    : 'Drag and drop PDF files'}
                </p>
                <p className="text-sm text-muted-foreground">
                  Or click to browse files
                </p>
                <p className="text-xs text-muted-foreground">
                  Supports multiple PDFs
                </p>
              </div>
              <Button variant="outline" size="sm">
                Select PDFs
              </Button>
            </>
          )}
        </div>

        {/* Processing Log */}
        {processingLog.length > 0 && (
          <div className="bg-muted rounded-lg p-4 space-y-2 max-h-48 overflow-y-auto">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Processing Log</p>
            <div className="space-y-1">
              {processingLog.map((log, index) => (
                <div key={index} className="flex items-start gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                  <span>{log}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upload Result */}
        {uploadResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2 text-green-800">
              <CheckCircle className="h-5 w-5" />
              <span className="font-semibold">Upload Successful!</span>
            </div>
            <div className="text-sm text-green-700 space-y-1">
              <p>Bank: {uploadResult.bank}</p>
              <p>Transactions: {uploadResult.transactionCount}</p>
              <div className="flex items-center gap-2">
                <span>Validation:</span>
                <span className={cn('px-2 py-0.5 rounded-full text-xs text-white', getValidationBadgeColor(uploadResult.validationStatus))}>
                  {uploadResult.validationStatus}
                </span>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
