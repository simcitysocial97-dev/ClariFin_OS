'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ImportDetectResult, ImportMapping } from '@/lib/api/client';

interface ImportPreviewProps {
  detectResult: ImportDetectResult;
  mapping: ImportMapping;
}

export function ImportPreview({ detectResult, mapping }: ImportPreviewProps) {
  // Apply mapping to sample rows to show preview
  const previewRows = detectResult.sample_rows.slice(0, 5).map((row) => {
    const rawDate = row[mapping.date_column] || '';
    const description = row[mapping.description_column] || '';
    const rawAmount = row[mapping.amount_column] || '';
    const rawType = mapping.type_column ? row[mapping.type_column] : '';
    
    // Parse amount (remove currency symbols, commas)
    const amount = parseFloat(rawAmount.replace(/[^0-9.-]/g, '')) || 0;
    
    // Determine type
    let type: 'debit' | 'credit' = 'debit';
    if (rawType) {
      const typeLower = rawType.toLowerCase();
      if (typeLower.includes('credit') || typeLower.includes('cr') || typeLower.includes('in')) {
        type = 'credit';
      }
    }
    
    return {
      date: rawDate,
      description,
      amount,
      type,
      category: 'Uncategorized',
    };
  });

  const totalDebit = previewRows
    .filter((r) => r.type === 'debit')
    .reduce((sum, r) => sum + r.amount, 0);
  
  const totalCredit = previewRows
    .filter((r) => r.type === 'credit')
    .reduce((sum, r) => sum + r.amount, 0);

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Import Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Rows</p>
              <p className="text-2xl font-bold">{detectResult.row_count}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Bank</p>
              <p className="text-lg font-medium">{mapping.bank_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Member</p>
              <p className="text-lg font-medium">{mapping.member}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Date Format</p>
              <p className="text-lg font-medium">{mapping.date_format}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
            <div>
              <p className="text-sm text-muted-foreground">Sample Debits</p>
              <p className="text-lg font-medium text-red-600">
                ₹{totalDebit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Sample Credits</p>
              <p className="text-lg font-medium text-green-600">
                ₹{totalCredit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Preview Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Preview (First 5 Rows)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="px-3 py-2 text-left font-medium">Date</th>
                  <th className="px-3 py-2 text-left font-medium">Description</th>
                  <th className="px-3 py-2 text-right font-medium">Amount</th>
                  <th className="px-3 py-2 text-center font-medium">Type</th>
                  <th className="px-3 py-2 text-left font-medium">Category</th>
                </tr>
              </thead>
              <tbody>
                {previewRows.map((row, i) => (
                  <tr key={i} className="border-b">
                    <td className="px-3 py-2">{row.date}</td>
                    <td className="px-3 py-2 max-w-xs truncate">{row.description}</td>
                    <td className="px-3 py-2 text-right">
                      ₹{row.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <Badge variant={row.type === 'credit' ? 'default' : 'secondary'}>
                        {row.type}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{row.category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Mapping Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Mapping Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Date Column:</span>
              <span className="font-medium">{mapping.date_column}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Description Column:</span>
              <span className="font-medium">{mapping.description_column}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Amount Column:</span>
              <span className="font-medium">{mapping.amount_column}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Type Column:</span>
              <span className="font-medium">{mapping.type_column || 'None'}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}