/**
 * Formatting Utilities
 * Re-exports from utils/format.ts for backward compatibility
 * 
 * @deprecated Import directly from '@/lib/utils/format' instead.
 */

// Re-export canonical formatters
export { formatINR, formatPaise, rupeesToPaise, paiseToRupees, formatPercentage, formatDateDisplay, truncateText, formatINRCompact } from './utils/format';

// Deprecated functions - kept for backward compatibility
/**
 * @deprecated Use formatINR instead. Backend should return paise values.
 */
export function formatRupees(rupees: number | null | undefined): string {
  if (rupees === null || rupees === undefined) return '—';
  const safeRupees = typeof rupees === 'number' && !isNaN(rupees) ? rupees : 0;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(safeRupees);
}

/**
 * @deprecated Use formatINRCompact instead. Backend should return paise values.
 */
export function formatRupeesCompact(rupees: number | null | undefined): string {
  if (rupees === null || rupees === undefined) return '—';
  const safeRupees = Math.abs(rupees);
  if (safeRupees >= 100000) {
    return `₹${(safeRupees / 100000).toFixed(1)}L`;
  }
  if (safeRupees >= 1000) {
    return `₹${(safeRupees / 1000).toFixed(1)}K`;
  }
  return formatRupees(rupees);
}
