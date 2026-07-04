/**
 * Formatting Utilities
 * Re-exports from utils/format.ts for backward compatibility
 */

export { formatPaise, rupeesToPaise, paiseToRupees, formatPercentage, formatDateDisplay, truncateText } from './utils/format';

/**
 * Format paise to INR display string (no decimal)
 */
export function formatINR(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) return '—';
  const safePaise = typeof paise === 'number' && !isNaN(paise) ? paise : 0;
  const rupees = safePaise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(rupees);
}

/**
 * Format paise to compact INR display (e.g., "₹12.5K" or "₹2.4L")
 */
export function formatINRCompact(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) return '—';
  const rupees = paise / 100;
  if (Math.abs(rupees) >= 100000) {
    return `₹${(rupees / 100000).toFixed(1)}L`;
  }
  if (Math.abs(rupees) >= 1000) {
    return `₹${(rupees / 1000).toFixed(1)}K`;
  }
  return formatINR(paise);
}