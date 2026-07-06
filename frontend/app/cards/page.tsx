'use client';

import { useStatements } from '@/lib/hooks/use-finance-data';
import { useAppStore } from '@/lib/store/use-app-store';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { CreditCard, Eye, Plus, CheckCircle, XCircle, AlertCircle, Calendar, FileText } from 'lucide-react';
import Link from 'next/link';
import { EmptyState } from '@/components/ui/empty-state';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { formatINR } from '@/lib/utils/format';
import type { Statement } from '@/lib/api/client';

// Map validation status to badge variant
function getValidationBadgeVariant(validationStatus: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (validationStatus) {
    case 'exact_match':
      return 'default'; // Green
    case 'close_match':
      return 'secondary'; // Amber/Yellow
    case 'mismatch':
      return 'destructive'; // Red
    case 'emi_exception':
      return 'default'; // Blue (using default with custom styling)
    case 'credit_balance':
      return 'outline'; // Gray
    default:
      return 'outline';
  }
}

// Get custom badge class for validation status
function getValidationBadgeClass(validationStatus: string): string {
  switch (validationStatus) {
    case 'exact_match':
      return 'bg-green-500 hover:bg-green-600';
    case 'close_match':
      return 'bg-amber-500 hover:bg-amber-600';
    case 'mismatch':
      return 'bg-red-500 hover:bg-red-600';
    case 'emi_exception':
      return 'bg-blue-500 hover:bg-blue-600';
    case 'credit_balance':
      return 'bg-gray-500 hover:bg-gray-600';
    default:
      return '';
  }
}

export default function CardsPage() {
  const { data: statements, loading, error, refetch } = useStatements();
  const { cards: localCards } = useAppStore();
  const { toast } = useToast();
  const [paidBills, setPaidBills] = useState<string[]>([]);

  // Show error toast
  useEffect(() => {
    if (error) {
      toast({
        title: 'Error loading statements',
        description: `${error.message}. Falling back to local data.`,
        variant: 'destructive',
      });
    }
  }, [error, toast]);

  // Fallback to local cards if API fails
  const hasApiData = statements && statements.length > 0;
  const hasLocalData = localCards.length > 0;
  const useLocalData = error && hasLocalData && !hasApiData;

  // Map local cards to statement format
  const localStatements: Statement[] = useLocalData
    ? localCards.map((card: any) => ({
        id: card.id,
        bank: card.bankName,
        file_name: '',
        card_last4: card.cardNumber.slice(-4),
        card_display: `•••• ${card.cardNumber.slice(-4)}`,
        period_from: card.billCycleStart || '',
        period_to: card.billCycleEnd || '',
        period_display: card.billCycleStart && card.billCycleEnd 
          ? `${new Date(card.billCycleStart).toLocaleDateString('en-IN', { month: 'short' })} - ${new Date(card.billCycleEnd).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}`
          : 'Unknown period',
        transaction_count: 0,
        // Canonical paise fields
        total_debit_paise: 0,
        total_credit_paise: 0,
        total_due_paise: card.totalAmountDue ? Math.round(card.totalAmountDue * 100) : 0,
        min_due_paise: card.minimumAmountDue ? Math.round(card.minimumAmountDue * 100) : 0,
        extracted_net_paise: 0,
        validation_difference_paise: 0,
        // Display fields
        total_debit_display: '₹0',
        total_credit_display: '₹0',
        total_due_display: formatINR(card.totalAmountDue ? Math.round(card.totalAmountDue * 100) : 0),
        extracted_net_display: '₹0',
        min_due_display: formatINR(card.minimumAmountDue ? Math.round(card.minimumAmountDue * 100) : 0),
        due_date: card.dueDate || '',
        validation_status: 'unknown',
        badge_text: 'Unknown',
        badge_color: 'gray',
      }))
    : [];

  const displayStatements = useLocalData ? localStatements : (statements || []);

  const handleMarkAsPaid = (id: string, bankName: string) => {
    setPaidBills([...paidBills, id]);
    toast({
      title: 'Bill marked as paid',
      description: `${bankName} bill has been marked as paid.`,
    });
  };

  const handleMarkAsUnpaid = (id: string, bankName: string) => {
    setPaidBills(paidBills.filter((billId: string) => billId !== id));
    toast({
      title: 'Bill marked as unpaid',
      description: `${bankName} bill has been marked as unpaid.`,
    });
  };

  const isBillPaid = (id: string) => paidBills.includes(id);

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <Skeleton className="h-10 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent className="space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <div className="flex gap-2 pt-4">
                  <Skeleton className="h-10 flex-1" />
                  <Skeleton className="h-10 flex-1" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Error state with no data
  if (error && !statements && !useLocalData) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Credit Cards</h1>
            <p className="text-muted-foreground mt-1">
              Manage your cards and view details
            </p>
          </div>
          <Link href="/?upload=true">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Card
            </Button>
          </Link>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error loading statements</AlertTitle>
          <AlertDescription>
            {error.message}. Please ensure the API server is running at http://localhost:8000
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const hasData = displayStatements.length > 0;

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Credit Cards</h1>
          <p className="text-muted-foreground mt-1">
            Manage your cards and view details {useLocalData && '(from local storage)'}
          </p>
        </div>
        <Link href="/?upload=true">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Card
          </Button>
        </Link>
      </div>

      {!hasData ? (
        <EmptyState
          icon={<CreditCard className="h-10 w-10" />}
          title="No cards yet"
          description="Upload your first bank statement to see your credit cards here. We'll automatically extract and display your card information."
          action={{
            label: "Upload Statement",
            href: "/?upload=true"
          }}
        />
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {displayStatements.map((statement: Statement) => {
            const paid = isBillPaid(String(statement.id));
            const badgeVariant = getValidationBadgeVariant(statement.validation_status);
            const badgeClass = getValidationBadgeClass(statement.validation_status);
            
            return (
              <Card key={statement.id} className="flex flex-col">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{statement.bank}</CardTitle>
                      <p className="text-sm text-muted-foreground">{statement.card_display}</p>
                    </div>
                    <Badge variant={badgeVariant} className={cn(badgeClass, 'text-white')}>
                      {statement.badge_text || statement.validation_status}
                    </Badge>
                  </div>
                </CardHeader>
                
                 <CardContent className="flex-1 space-y-3 p-4">
                   {/* Statement Period */}
                   <div className="flex items-center gap-2 text-sm">
                     <Calendar className="h-4 w-4 text-muted-foreground" />
                     <span className="text-muted-foreground">Period:</span>
                     <span>{statement.period_display}</span>
                   </div>

                   {/* Transaction Count */}
                   <div className="flex items-center gap-2 text-sm">
                     <FileText className="h-4 w-4 text-muted-foreground" />
                     <span className="text-muted-foreground">Transactions:</span>
                     <span>{statement.transaction_count}</span>
                   </div>

                   {/* Total Debits / Credits */}
                   <div className="grid grid-cols-2 gap-4 py-2 border-y">
                     <div>
                       <p className="text-xs text-muted-foreground">Total Debits</p>
                       <p className="text-sm font-medium text-red-600">{statement.total_debit_display}</p>
                     </div>
                     <div>
                       <p className="text-xs text-muted-foreground">Total Credits</p>
                       <p className="text-sm font-medium text-green-600">{statement.total_credit_display}</p>
                     </div>
                   </div>

                   {/* Validation Section */}
                   <div className="space-y-2 bg-muted/50 rounded-lg p-3">
                     <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Validation</p>
                     
                     <div className="flex items-center justify-between text-sm">
                       <span className="text-muted-foreground">Statement Total Due:</span>
                       <span className="font-medium">{statement.total_due_display}</span>
                     </div>
                     
                     <div className="flex items-center justify-between text-sm">
                       <span className="text-muted-foreground">Extracted Net:</span>
                       <span className="font-medium">{statement.extracted_net_display}</span>
                     </div>
                     
                     {statement.validation_difference_paise !== undefined && statement.validation_difference_paise !== 0 && (
                       <div className="flex items-center justify-between text-sm">
                         <span className="text-muted-foreground">Difference:</span>
                         <span className={cn(
                           'font-medium',
                           statement.validation_difference_paise > 0 ? 'text-red-600' : 'text-amber-600'
                         )}>
                           ₹{Math.abs(statement.validation_difference_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                         </span>
                       </div>
                     )}
                   </div>

                   {/* Due Date & Minimum Due */}
                   {statement.due_date && (
                     <div className="flex items-center justify-between text-sm">
                       <div className="flex items-center gap-2">
                         <AlertCircle className="h-4 w-4 text-muted-foreground" />
                         <span className="text-muted-foreground">Due:</span>
                       </div>
                       <span>{new Date(statement.due_date).toLocaleDateString('en-IN')}</span>
                     </div>
                   )}
                   
                   {statement.min_due_display && statement.min_due_display !== '₹0.00' && (
                     <div className="flex items-center justify-between text-sm">
                       <span className="text-muted-foreground">Minimum Due:</span>
                       <span>{statement.min_due_display}</span>
                     </div>
                   )}

                   {/* Action Buttons */}
                   <div className="flex gap-2 pt-2">
                     <Link href={`/transactions?cardId=${statement.id}`} className="flex-1">
                       <Button variant="outline" size="sm" className="w-full">
                         <Eye className="mr-2 h-4 w-4" />
                         View
                       </Button>
                     </Link>
                     
                     {!paid && statement.due_date && new Date(statement.due_date) > new Date() && (
                       <Button
                         variant="outline"
                         size="sm"
                         className="flex-1 bg-green-50 hover:bg-green-100 text-green-700 border-green-200"
                         onClick={() => handleMarkAsPaid(String(statement.id), statement.bank)}
                       >
                         <CheckCircle className="mr-2 h-4 w-4" />
                         Mark Paid
                       </Button>
                     )}
                     
                     {paid && (
                       <Button
                         variant="outline"
                         size="sm"
                         className="flex-1"
                         onClick={() => handleMarkAsUnpaid(String(statement.id), statement.bank)}
                       >
                         <XCircle className="mr-2 h-4 w-4" />
                         Mark Unpaid
                       </Button>
                     )}
                   </div>
                 </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}