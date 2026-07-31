# Mapper Layer Documentation

## Overview

The Mapper Layer transforms backend DTOs to ViewModels for the Transaction Intelligence Workspace. It ensures clean separation between backend data and frontend presentation.

## Architecture Flow

```
Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components
```

## TransactionMapper

### Interface

```typescript
interface ITransactionMapper {
  mapTransaction(dto: TransactionDTO): TransactionViewModel;
  mapTransactions(dtos: TransactionDTO[]): TransactionViewModel[];
}
```

### Usage

```typescript
import { transactionMapper } from '@/lib/mappers/transaction-mapper';

// Single transaction
const viewModel = transactionMapper.mapTransaction(dto);

// Multiple transactions
const viewModels = transactionMapper.mapTransactions(dtos);
```

### Key Transformations

1. **Date Formatting**: Converts ISO date to formatted display date
2. **Amount Formatting**: Converts paise to MoneyViewModel
3. **Evidence Mapping**: Transforms evidence data to ViewModel format
4. **Import Lineage**: Maps import history to lineage structure
5. **Selection State**: Initializes selection state to default values

## Formatter Utilities

```typescript
// Format paise to display string
formatPaise(paise: number): string;

// Format date to display string
formatDate(date: string): string;

// Format month key (YYYY-MM)
formatMonthKey(date: string): string;

// Slugify string for URLs
slugify(str: string): string;
```

## Error Handling

The mapper handles malformed DTO data gracefully:
- Returns null for invalid data
- Throws descriptive errors for missing required fields
- Logs warnings for unexpected data structures