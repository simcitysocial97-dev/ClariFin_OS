/**
 * Chart Colors - Shared color tokens for chart visualization
 *
 * Uses CSS variables for theme consistency.
 */

/**
 * Color tokens for chart elements
 * All colors use CSS variables for theme support
 */
export const CHART_COLORS = {
  // Primary action color (income, positive values)
  primary: 'hsl(var(--primary))',
  
  // Destructive/error color (expense, negative values)
  destructive: 'hsl(var(--destructive))',
  
  // Success color (net savings, positive trends)
  success: 'hsl(var(--green-600))',
  
  // Muted foreground (axis ticks, grid lines)
  mutedForeground: 'hsl(var(--muted-foreground))',
  
  // Popover background (tooltips)
  popover: 'hsl(var(--popover))',
  
  // Border (tooltips, cards)
  border: 'hsl(var(--border))',
  
  // Popover foreground (tooltips)
  popoverForeground: 'hsl(var(--popover-foreground))',
} as const;

/**
 * Gradient definitions for chart fills
 * These are used in <defs> within charts
 */
export const CHART_GRADIENTS = {
  income: {
    id: 'incomeBar',
    startColor: CHART_COLORS.primary,
    endColor: CHART_COLORS.primary,
    startOpacity: 0.8,
    endOpacity: 0.6,
  },
  expense: {
    id: 'expenseBar',
    startColor: CHART_COLORS.destructive,
    endColor: CHART_COLORS.destructive,
    startOpacity: 0.8,
    endOpacity: 0.6,
  },
} as const;

/**
 * Get gradient fill URL
 */
export function getGradientFill(gradientId: string): string {
  return `url(#${gradientId})`;
}