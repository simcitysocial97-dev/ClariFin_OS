/**
 * Shared Formatters - Stage 3 Transaction Intelligence Workspace
 *
 * Reusable formatting logic for dates, amounts, and currency.
 */

/**
 * Format paise to Indian Rupee display string
 * @param paise - Amount in paise (₹1.00 = 100 paise)
 * @returns Formatted string like "₹1,234.56" or "-₹1,234.56"
 */
export function formatPaise(paise: number): string {
  const rupees = paise / 100;
  const sign = rupees < 0 ? '-' : '';
  const absRupees = Math.abs(rupees);
  return `${sign}₹${absRupees.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Format date to Indian locale
 * @param dateString - ISO date string
 * @returns Formatted date like "Jul 5, 2026"
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format date to month key for grouping
 * @param dateString - ISO date string
 * @returns Month key like "2026-07"
 */
export function formatMonthKey(dateString: string): string {
  const date = new Date(dateString);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

/**
 * Slugify a string for ID generation
 * @param str - Input string
 * @returns Slugified string
 */
export function slugify(str: string): string {
  return str.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
}