'use client';

import { useState, useEffect } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMember } from '@/lib/context/member-context';
import type { ImportDetectResult, ImportMapping } from '@/lib/api/client';

interface ColumnMapperProps {
  detectResult: ImportDetectResult;
  onMappingChange: (mapping: ImportMapping) => void;
}

const DATE_FORMATS = [
  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (31/12/2024)' },
  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (12/31/2024)' },
  { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD (2024-12-31)' },
  { value: 'DD-MM-YYYY', label: 'DD-MM-YYYY (31-12-2024)' },
  { value: 'MM-DD-YYYY', label: 'MM-DD-YYYY (12-31-2024)' },
  { value: 'DD-Mon-YYYY', label: 'DD-Mon-YYYY (31-Dec-2024)' },
  { value: 'DD-MON-YY', label: 'DD-MON-YY (31-DEC-24)' },
];

export function ColumnMapper({ detectResult, onMappingChange }: ColumnMapperProps) {
  const { member, members } = useMember();
  const [mapping, setMapping] = useState<ImportMapping>({
    date_column: detectResult.detected_mapping.date_column || '',
    description_column: detectResult.detected_mapping.description_column || '',
    amount_column: detectResult.detected_mapping.amount_column || '',
    type_column: detectResult.detected_mapping.type_column || '',
    bank_name: 'Manual Import',
    member: member === 'All' ? 'Self' : member,
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
      {/* Column Mapping */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Column Mapping</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Date Column */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Date Column <span className="text-destructive">*</span>
            </label>
            <Select
              value={mapping.date_column}
              onValueChange={(v) => updateMapping('date_column', v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select date column" />
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
              Description Column <span className="text-destructive">*</span>
            </label>
            <Select
              value={mapping.description_column}
              onValueChange={(v) => updateMapping('description_column', v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select description column" />
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
              Amount Column <span className="text-destructive">*</span>
            </label>
            <Select
              value={mapping.amount_column}
              onValueChange={(v) => updateMapping('amount_column', v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select amount column" />
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
              Type Column <span className="text-muted-foreground">(optional)</span>
            </label>
            <Select
              value={mapping.type_column || 'none'}
              onValueChange={(v) => updateMapping('type_column', v === 'none' ? '' : v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type column (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None (all treated as debit)</SelectItem>
                {detectResult.columns.map((col) => (
                  <SelectItem key={col} value={col}>
                    {col}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Import Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Import Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Bank Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Bank Name</label>
            <Input
              value={mapping.bank_name}
              onChange={(e) => updateMapping('bank_name', e.target.value)}
              placeholder="Enter bank name"
            />
          </div>

          {/* Member */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Member</label>
            <Select
              value={mapping.member}
              onValueChange={(v) => updateMapping('member', v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select member" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Self">Self</SelectItem>
                {members.map((m) => (
                  <SelectItem key={m.id} value={m.name}>
                    {m.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Date Format */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Date Format</label>
            <Select
              value={mapping.date_format}
              onValueChange={(v) => updateMapping('date_format', v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select date format" />
              </SelectTrigger>
              <SelectContent>
                {DATE_FORMATS.map((fmt) => (
                  <SelectItem key={fmt.value} value={fmt.value}>
                    {fmt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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