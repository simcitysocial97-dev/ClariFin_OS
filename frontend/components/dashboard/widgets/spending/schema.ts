import { z } from 'zod';

// Category spend item from /api/categories response
export const CategorySpendSchema = z.object({
  category: z.string(),
  amount: z.number(),
  amount_display: z.string(),
  count: z.number().int().nonnegative(),
  percentage: z.number().nonnegative(),
});

// Summary by category
export const CategorySummarySchema = z.object({
  summary: z.array(CategorySpendSchema),
  monthly_breakdown: z.array(z.record(z.string(), z.number())),
  drill_transactions: z.array(z.record(z.string(), z.unknown())),
  uncategorized_patterns: z.array(z.object({
    description: z.string(),
    count: z.number().int().nonnegative(),
    total_display: z.string(),
  })),
});

// Top merchant from /api/analytics response
export const TopMerchantSchema = z.object({
  merchant: z.string(),
  amount_display: z.string(),
  count: z.number().int().nonnegative(),
});

// Analytics response used by MerchantWidget
export const AnalyticsMerchantsSchema = z.object({
  top_merchants: z.array(TopMerchantSchema),
});

// Export types
export type CategorySpend = z.infer<typeof CategorySpendSchema>;
export type CategorySummary = z.infer<typeof CategorySummarySchema>;
export type TopMerchant = z.infer<typeof TopMerchantSchema>;