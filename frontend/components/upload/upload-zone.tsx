'use client';

import { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { useAppStore } from '@/lib/store/use-app-store';
import { Upload, FileText, Bug } from 'lucide-react';
import { cn } from '@/lib/utils';

// Dynamic import of parser to avoid SSR issues
let parseStatement: any;
const loadParser = async () => {
  if (!parseStatement) {
    const module = await import('@/lib/parser');
    parseStatement = module.parseStatement;
  }
  return parseStatement;
};

// Extend Window interface for debug functions
declare global {
  interface Window {
    initParserDebug?: (total: number) => void;
    updateParserDebug?: (entry: {
      fileName: string;
      transactions: number;
      success: boolean;
      duration: number;
    }) => void;
    showParserDebug?: () => void;
    __DEBUG_PARSER__?: boolean;
  }
}

export function UploadZone() {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [parsedFiles, setParsedFiles] = useState(0);
  const [debugEnabled, setDebugEnabled] = useState(false);
  const { toast } = useToast();
  const { addCard, addTransactions } = useAppStore();

  // Check if debug mode is enabled
  useEffect(() => {
    setDebugEnabled(window.__DEBUG_PARSER__ || false);
  }, []);

  // Enable debug mode
  const enableDebug = useCallback(() => {
    window.__DEBUG_PARSER__ = true;
    setDebugEnabled(true);
    toast({
      title: 'Debug mode enabled',
      description: 'Parser debug panel will show during uploads',
    });
  }, [toast]);

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

      // Initialize debug panel if debug mode is enabled
      if (window.__DEBUG_PARSER__ && window.initParserDebug) {
        window.initParserDebug(acceptedFiles.length);
        window.showParserDebug?.();
      }

      // Process each file sequentially
      let successCount = 0;
      let failCount = 0;
      let totalTransactions = 0;

      for (let i = 0; i < acceptedFiles.length; i++) {
        const file = acceptedFiles[i];
        const fileProgress = Math.round((i / acceptedFiles.length) * 100);
        setProgress(fileProgress);

        try {
          // Capture ArrayBuffer immediately to avoid zero-byte issues
          const arrayBuffer = await file.arrayBuffer();
          if (!arrayBuffer || arrayBuffer.byteLength === 0) {
            throw new Error(
              `File "${file.name}" is empty or could not be read`
            );
          }

          // Track parse start time
          const startTime = Date.now();

          // Load parser and parse
          console.warn('[UPLOAD] Loading parser...');
          const parser = await loadParser();
          console.warn('[UPLOAD] Calling parseStatement...');
          const result = await parser(file);
          console.warn('[UPLOAD] Parse result:', result);

          const endTime = Date.now();
          const duration = endTime - startTime;

          // Update debug panel
          if (window.__DEBUG_PARSER__ && window.updateParserDebug) {
            window.updateParserDebug({
              fileName: result.fileName || file.name,
              transactions: result.transactions?.length || 0,
              success: true,
              duration: duration,
            });
          }

          // Add card with all required fields
          const card = {
            id: crypto.randomUUID(),
            bankName: result.metadata.bankName,
            cardNumber: result.metadata.cardNumber || '',
            creditLimit: result.metadata.creditLimit || 0,
            totalAmountDue: result.metadata.totalAmountDue || 0,
            minimumAmountDue: result.metadata.minimumAmountDue || 0,
            dueDate: result.metadata.dueDate || '',
            billCycleStart: result.metadata.billCycleStart || '',
            billCycleEnd: result.metadata.billCycleEnd || '',
            openingBalance: result.metadata.openingBalance,
          };
          addCard(card);

           // Add transactions with all required fields
           const transactionsWithCardId = result.transactions.map((t: any) => ({
             id: crypto.randomUUID(),
             date: t.date,
             description: t.description,
             amount_paise: t.amount_paise,
             type: t.type as 'debit' | 'credit',
             category: t.category,
             bank: result.metadata.bankName,
             cardId: card.id,
           }));
          addTransactions(transactionsWithCardId);

          successCount++;
          totalTransactions += result.transactions.length;
          setParsedFiles((prev) => prev + 1);
        } catch (error) {
          console.error(`[PDF-PARSER ERROR] ${file.name}:`, error);

          // Update debug panel with failure
          if (window.__DEBUG_PARSER__ && window.updateParserDebug) {
            window.updateParserDebug({
              fileName: file.name,
              transactions: 0,
              success: false,
              duration: 0,
            });
          }

          failCount++;
          setParsedFiles((prev) => prev + 1);
        }
      }

      setProgress(100);

      // Show final toast
      if (successCount > 0) {
        toast({
          title: `Upload complete!`,
          description: `Successfully parsed ${successCount} PDF(s) with ${totalTransactions} transactions. ${failCount > 0 ? `${failCount} failed.` : ''}`,
        });
      } else {
        toast({
          title: 'Upload failed',
          description: `All ${failCount} PDF(s) failed to parse`,
          variant: 'destructive',
        });
      }

      setTimeout(() => {
        setIsUploading(false);
        setProgress(0);
        setTotalFiles(0);
        setParsedFiles(0);
      }, 2000);
    },
    [addCard, addTransactions, toast]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 10, // Allow up to 10 files
    disabled: isUploading,
    multiple: true, // Enable multiple file selection
  });

  return (
    <div className="space-y-4">
      {/* Debug Mode Toggle */}
      <div className="flex justify-end">
        <Button
          variant={debugEnabled ? 'default' : 'outline'}
          size="sm"
          onClick={enableDebug}
          disabled={debugEnabled}
          className="gap-2"
        >
          <Bug className="h-4 w-4" />
          {debugEnabled ? 'Debug Enabled' : 'Enable Debug'}
        </Button>
      </div>

      <Card className="border-dashed border-2 hover:border-primary/50 transition-colors">
        <CardContent className="p-8">
          <div
            {...getRootProps()}
            className={cn(
              'flex flex-col items-center justify-center gap-4 text-center cursor-pointer',
              isDragActive && 'text-primary',
              isUploading && 'pointer-events-none opacity-50'
            )}
          >
            <input {...getInputProps()} />

            {isUploading ? (
              <>
                <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
                  <FileText className="h-8 w-8 text-primary" />
                </div>
                <div className="space-y-2 w-full max-w-xs">
                  <p className="text-sm font-medium">
                    Parsing PDFs... ({parsedFiles}/{totalFiles})
                  </p>
                  <Progress value={progress} className="h-2" />
                  <p className="text-xs text-muted-foreground">
                    {progress === 100
                      ? 'Complete!'
                      : 'Processing files sequentially...'}
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                  <Upload className="h-8 w-8 text-primary" />
                </div>
                <div className="space-y-2">
                  <p className="text-lg font-medium">
                    {isDragActive
                      ? 'Drop your PDFs here'
                      : 'Upload your bank statements'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Drag and drop PDF files, or click to browse
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Supports multiple PDFs: HDFC, ICICI, SBI, Axis, IDFC, and
                    more
                  </p>
                </div>
                <Button variant="outline" className="mt-2">
                  Select PDFs
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
