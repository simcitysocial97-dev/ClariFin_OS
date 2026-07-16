import { useQuery } from '@tanstack/react-query';
import { CategorySummarySchema, type CategorySummary } from './schema';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

async function fetchCategories(): Promise<CategorySummary> {
  const response = await fetch(`${API_BASE}/api/categories`);
  if (!response.ok) {
    throw new Error(`Categories fetch failed: ${response.status}`);
  }
  const data = await response.json();
  return CategorySummarySchema.parse(data);
}

export function useSpending() {
  return useQuery({
    queryKey: ['spending', 'categories'],
    queryFn: fetchCategories,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}