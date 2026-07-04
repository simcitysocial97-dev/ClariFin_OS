'use client';

import { useState, useEffect } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ImportDetectResult, ImportMapping } from '@/lib/api/client';

interface ColumnMapperProps {
  detectResult: ImportDetectResult;
  onMappingChange: (mapping: ImportMapping) => void;
}

export function ColumnMapper({ detectResult, onMappingChange }: ColumnMapperProps) {
  const [mapping, setMapping] = useState<ImportMapping>({
    date_column: detectResult.detected_mapping.date_column || '',
    description_column: detectResult.detected_mapping.description_column || '',
    amount_column: detectResult.detected_mapping.amount_column || '',
    type_column: detectResult.detected_mapping.type_column || '',
    bank_name: 'Manual Import',
    member: 'Self', // Default to Self, no selector needed
    date_format: detectResult.detected_mapping.date_format || 'DD/MM/YYYY',
  });

  useEffect(() => {
    onMappingChange(mapping);
  }, [mapping, onMappingChange]);

  const updateMapping = <K extends keyof ImportMapping>(key: K, value: ImportMapping[K]) => {
    setMapping((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Column Mapping - Horizontal Layout */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Column Mapping</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Date Column */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Date <span className="text-destructive">*</span>
              </label>
              <Select
                value={mapping.date_column}
                onValueChange={(v) => updateMapping('date_column', v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent>
                  {detectResult.columns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Description Column */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Description <span className="text-destructive">*</span>
              </label>
              <Select
                value={mapping.description_column}
                onValueChange={(v) => updateMapping('description_column', v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent>
                  {detectResult.columns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Amount Column */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Amount <span className="text-destructive">*</span>
              </label>
              <Select
                value={mapping.amount_column}
                onValueChange={(v) => updateMapping('amount_column', v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent>
                  {detectResult.columns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Type Column (Optional) */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Type <span className="text-muted-foreground">(optional)</span>
              </label>
              <Select
                value={mapping.type_column || 'none'}
                onValueChange={(v) => updateMapping('type_column', v === 'none' ? '' : v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Optional" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {detectResult.columns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>


      {/* Sample Data Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Sample Data ({detectResult.row_count} rows detected)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  {detectResult.columns.map((col) => (
                    <th key={col} className="px-2 py-2 text-left font-medium">
                      {col}
                      {col === mapping.date_column && (
                        <span className="ml-1 text-xs text-blue-500">(Date)</span>
                      )}
                      {col === mapping.description_column && (
                        <span className="ml-1 text-xs text-green-500">(Desc)</span>
                      )}
                      {col === mapping.amount_column && (
                        <span className="ml-1 text-xs text-amber-500">(Amt)</span>
                      )}
                      {col === mapping.type_column && (
                        <span className="ml-1 text-xs text-purple-500">(Type)</span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {detectResult.sample_rows.slice(0, 5).map((row, i) => (
                  <tr key={i} className="border-b">
                    {detectResult.columns.map((col) => (
                      <td key={col} className="px-2 py-2 text-muted-foreground">
                        {row[col]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
