# Evidence System Documentation

## Overview

The Evidence System provides explainability for all transaction insights in the Transaction Intelligence Workspace.

## Evidence Types

```typescript
type EvidenceType = 'categorization' | 'import' | 'adjustment' | 'balance' | 'reconciliation';
```

## Components

### EvidenceDrawer
Main drawer component that displays evidence for a selected transaction.
- Responsive design (full-width on mobile)
- Dark mode support
- Accessibility with ARIA labels

### EvidenceSummary
Displays summary statistics for evidence items.
- Count of evidence items
- Breakdown by type
- Average confidence score

### EvidenceList
Renders a list of evidence items.
- Loading state
- Error state
- Empty state

### EvidenceItemComponent
Renders a single evidence item.
- Type badge with color coding
- Summary text
- Source link
- Confidence score

### EvidenceSourceLink
Displays source information for an evidence item.
- File ID
- Row number
- Extraction ID

### EvidenceCalculationView
Displays the calculation chain for evidence.
- Step-by-step derivation
- Input/output values

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
  openEvidence,
  closeEvidence,
} = useEvidence();
```

## Factories

```typescript
// Create categorization evidence
createCategorizationEvidence(summary, source, confidence);

// Create import evidence
createImportEvidence(summary, source, confidence?);

// Create adjustment evidence
createAdjustmentEvidence(summary, source, confidence?);

// Create balance evidence
createBalanceEvidence(summary, source, confidence?);

// Create reconciliation evidence
createReconciliationEvidence(summary, source, confidence?);
```

## Architecture

The evidence system follows the presentation-only pattern:
- Components render and emit events
- No fetching or business logic in components
- Evidence data is provided by the capability layer
- All evidence is derived from backend calculations