# TransactionViewModel Documentation

## Overview

The TransactionViewModel is the canonical data structure for displaying transaction data in the Transaction Intelligence Workspace. It provides all fields needed for display, explainability, and navigation.

## Type Definition

```typescript
interface TransactionViewModel {
  // Core Fields
  id: string;
  date: string;
  description: string;
  amount: MoneyViewModel;

  // Date Navigation
  year: number;
  month: number;
  day: number;
  month_key: string;
  date_formatted: string;

  // Category Navigation
  category_id: string | null;
  category_name: string | null;
  category_path: string | null;

  // Merchant Navigation
  merchant_id: string | null;
  merchant_name: string | null;
  merchant_category: string | null;

  // Account Reference
  account_id: string;
  account_name: string;
  bank: string;

  // Transaction Type
  transaction_type: 'debit' | 'credit' | 'transfer';
  reference_number: string | null;

  // Selection State
  selected: boolean;
  selectable: boolean;
  selection_reason: string | null;

  // Adjustment Visibility
  is_adjusted: boolean;
  adjustment_id: string | null;
  adjustment_reason: string | null;

  // Import Lineage
  import_lineage: ImportLineage | null;

  // Evidence System
  evidence: EvidenceItem[];
  calculation_chain: CalculationStep[];

  // Source Reference
  source_reference: SourceReference | null;

  // Reconciliation Reference
  reconciliation_id: string | null;
  reconciliation_status: 'pending' | 'confirmed' | 'rejected' | null;

  // Confidence Score
  confidence: number | null;
}
```

## MoneyViewModel

```typescript
interface MoneyViewModel {
  paise: number;    // Canonical value (1 INR = 100 paise)
  rupees: number;   // Display value (paise / 100)
}
```

## Usage Examples

### Basic Transaction Display

```tsx
import type { TransactionViewModel } from '@/types/transaction-view-model';

function TransactionRow({ transaction }: { transaction: TransactionViewModel }) {
  return (
    <tr>
      <td>{transaction.date_formatted}</td>
      <td>{transaction.description}</td>
      <td className={transaction.amount.paise >= 0 ? 'text-green-600' : 'text-red-600'}>
        {formatPaise(transaction.amount.paise)}
      </td>
      <td>{transaction.category_name}</td>
    </tr>
  );
}
```

### Evidence Access

```tsx
function TransactionEvidence({ transaction }: { transaction: TransactionViewModel }) {
  return (
    <div>
      <h3>Evidence ({transaction.evidence.length} items)</h3>
      {transaction.evidence.map((item, index) => (
        <div key={index}>
          <span>{item.type}</span>
          <span>{item.summary}</span>
          {item.confidence && <span>Confidence: {item.confidence}%</span>}
        </div>
      ))}
    </div>
  );
}
```

## Architecture Notes

- All monetary values use integer paise for financial determinism
- Evidence array provides explainability for all insights
- Import lineage tracks data provenance
- Selection state enables bulk operations
- Navigation fields enable cross-workspace navigation