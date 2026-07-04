'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

// Supported bank formats
const BANK_FORMATS = [
  { value: 'auto', label: 'Auto-Detect' },
  { value: 'hdfc', label: 'HDFC Bank' },
  { value: 'sbi', label: 'State Bank of India (SBI)' },
  { value: 'icici', label: 'ICICI Bank' },
  { value: 'axis', label: 'Axis Bank' },
  { value: 'idfc', label: 'IDFC Bank' },
  { value: 'indusind', label: 'IndusInd Bank' },
  { value: 'manual', label: 'Manual / Other' },
] as const;

export type BankFormat = typeof BANK_FORMATS[number]['value'];

interface ParserConfigurationProps {
  selectedFormat: BankFormat;
  onFormatChange: (format: BankFormat) => void;
  disabled?: boolean;
}

export function ParserConfiguration({
  selectedFormat,
  onFormatChange,
  disabled = false,
}: ParserConfigurationProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Parser Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="bank-format">Bank Format</Label>
          <Select
            value={selectedFormat}
            onValueChange={(value) => onFormatChange(value as BankFormat)}
            disabled={disabled}
          >
            <SelectTrigger id="bank-format" className="w-full">
              <SelectValue placeholder="Select bank format" />
            </SelectTrigger>
            <SelectContent>
              {BANK_FORMATS.map((bank) => (
                <SelectItem key={bank.value} value={bank.value}>
                  {bank.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Select your bank format for optimal parsing. Choose &quot;Auto-Detect&quot; to let the system identify the format automatically.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
