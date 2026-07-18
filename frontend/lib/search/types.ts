/**
 * Search Types - Stage 3 Transaction Intelligence Workspace
 *
 * Type definitions for transaction search.
 */

// Search result type
export interface SearchResult {
  id: string;
  highlight: string;
  matches: SearchMatch[];
}

// Search match type
export interface SearchMatch {
  field: 'description' | 'merchant' | 'category';
  value: string;
  indices: [number, number][]; // Start and end positions for highlighting
}

// Search state
export interface SearchState {
  query: string;
  debouncedQuery: string;
  results: SearchResult[];
  loading: boolean;
  error: string | null;
  history: string[];
}