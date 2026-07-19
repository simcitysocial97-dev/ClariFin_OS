# Loading/Error States - Stage 3 Transaction Intelligence Workspace

## Overview

This module provides loading, error, and empty state components for the Transaction Intelligence Workspace.

## Components

### LoadingSpinner

A spinning loader with size variants for loading states.

```tsx
import { LoadingSpinner } from '@/components/loading';

// Default size (md)
<LoadingSpinner />

// Small size
<LoadingSpinner size="sm" />

// Large size
<LoadingSpinner size="lg" />
```

**Props:**
- `size`: 'sm' | 'md' | 'lg' (default: 'md')
- `className`: Optional CSS class name

### SkeletonRow

Placeholder row for table loading state.

```tsx
import { SkeletonRow, SkeletonTable } from '@/components/loading';

// Single row with 7 columns
<SkeletonRow />

// Multiple rows
<SkeletonTable rows={5} columns={7} />
```

**Props:**
- `columns`: Number of columns (default: 7)

### ErrorMessage

Error display with optional retry button.

```tsx
import { ErrorMessage } from '@/components/loading';

// Basic error
<ErrorMessage message="Failed to load transactions" />

// With retry
<ErrorMessage 
  message="Failed to load transactions" 
  onRetry={() => refetch()} 
/>

// Custom title
<ErrorMessage 
  title="Network Error" 
  message="Please check your connection" 
/>
```

**Props:**
- `title`: Error title (default: 'Error')
- `message`: Error message (required)
- `onRetry`: Optional retry callback

### EmptyState

Message when no transactions are found.

```tsx
import { EmptyState } from '@/components/loading';

// Default
<EmptyState />

// With action
<EmptyState 
  title="No results"
  description="Try a different search"
  onAction={clearFilters}
/>
```

**Props:**
- `title`: State title (default: 'No transactions found')
- `description`: State description (default: 'Try adjusting your filters or search query.')
- `actionLabel`: Action button text (default: 'Clear filters')
- `onAction`: Optional action callback

## Accessibility

All components include proper ARIA attributes:
- `LoadingSpinner`: `role="status"` and `aria-label="Loading"`
- `ErrorMessage`: `role="alert"`
- `EmptyState`: Uses the underlying UI EmptyState component

## Dark Mode

All components support dark mode with appropriate color variants.