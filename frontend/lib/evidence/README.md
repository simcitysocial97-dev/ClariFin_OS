# Evidence System

The Evidence System provides explainability and traceability for transaction data in the Transaction Intelligence Workspace.

## Overview

Every insight in the workspace must expose:
- **Summary** - Human-readable description of the evidence
- **Evidence** - Supporting data and references
- **Calculation** - Step-by-step derivation of values
- **Source** - Original data source reference

## Types

### EvidenceType
```typescript
type EvidenceType = 'categorization' | 'import' | 'adjustment' | 'balance' | 'reconciliation';
```

### EvidenceItem
```typescript
interface EvidenceItem {
  type: EvidenceType;
  summary: string;
  source: EvidenceSource;
  confidence?: number; // 0-100
}
```

### EvidenceSource
```typescript
interface EvidenceSource {
  file_id?: string;
  row_number?: number;
  extraction_id?: string;
  api_endpoint?: string;
}
```

## Components

### EvidenceDrawer
The main drawer component that displays evidence for a selected transaction.

```tsx
<EvidenceDrawer state={evidenceState} onClose={handleClose} />
```

### EvidenceSummary
Displays summary statistics for evidence items.

```tsx
<EvidenceSummary count={5} byType={{ categorization: 2, import: 3 }} averageConfidence={85} />
```

### EvidenceList
Renders a list of evidence items with loading and error states.

```tsx
<EvidenceList evidence={items} loading={false} error={null} />
```

### EvidenceItemComponent
Renders a single evidence item with type badge, summary, and source link.

```tsx
<EvidenceItemComponent item={evidenceItem} />
```

### EvidenceSourceLink
Displays source information for an evidence item.

```tsx
<EvidenceSourceLink source={evidenceItem.source} />
```

### EvidenceCalculationView
Displays the calculation chain for evidence.

```tsx
<EvidenceCalculationView steps={calculationSteps} />
```

## Hook

### useEvidence
React hook for evidence state management.

```typescript
const {
  isOpen,
  transactionId,
  evidence,
  loading,
  error,
  toggleEvidence,
  openEvidence,
  closeEvidence,
} = useEvidence();
```

## Factories

Factory functions for creating evidence items:

- `createCategorizationEvidence(summary, source, confidence)`
- `createImportEvidence(summary, source, confidence?)`
- `createAdjustmentEvidence(summary, source, confidence?)`
- `createBalanceEvidence(summary, source, confidence?)`
- `createReconciliationEvidence(summary, source, confidence?)`

## Usage

```tsx
import { useEvidence } from '@/lib/evidence';
import { createCategorizationEvidence } from '@/lib/evidence';

function TransactionRow({ transaction }) {
  const { openEvidence } = useEvidence();
  
  const handleClick = () => {
    const evidence = [
      createCategorizationEvidence(
        'Categorized as Food',
        { file_id: transaction.file_id, row_number: transaction.row_number },
        95
      ),
    ];
    openEvidence(transaction.id, evidence);
  };
  
  return <tr onClick={handleClick}>...</tr>;
}
```

## Architecture

The evidence system follows the presentation-only pattern:
- Components render and emit events
- No fetching or business logic in components
- Evidence data is provided by the capability layer
- All evidence is derived from backend calculations