# Search Engine

## Overview

The Search Engine provides transaction search functionality for the Transaction Intelligence Workspace.

## Components

### TransactionSearch

Text input component for searching transactions.

**Props:**
- `value: string` - Current search query
- `onChange: (query: string) => void` - Callback when query changes
- `placeholder?: string` - Placeholder text (default: "Search transactions...")

**Features:**
- 300ms debounce on input
- Clear button
- Search icon
- Responsive design

## Types

### SearchResult
- `id: string` - Transaction ID
- `highlight: string` - Highlighted text
- `matches: SearchMatch[]` - Array of match details

### SearchMatch
- `field: 'description' | 'merchant' | 'category'` - Field that matched
- `value: string` - Matched value
- `indices: [number, number][]` - Positions for highlighting

### SearchState
- `query: string` - Current query
- `debouncedQuery: string` - Debounced query
- `results: SearchResult[]` - Search results
- `loading: boolean` - Loading state
- `error: string | null` - Error message
- `history: string[]` - Search history

## Usage

```tsx
import { TransactionSearch } from '@/lib/search';

function TransactionWorkspace() {
  const [query, setQuery] = useState('');

  return (
    <TransactionSearch
      value={query}
      onChange={setQuery}
    />
  );
}
```

## Architecture

The search component follows the presentation-only pattern:
- No data fetching
- No business logic
- Emits events via onChange
- Uses debounce for performance