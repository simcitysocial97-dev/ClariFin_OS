/**
 * Formatting Utilities
 * 
 * Phase 1: Functions for formatting paise values to display strings.
 * All financial calculations should use paise (INTEGER), display uses formatted strings.
 * 
 * Canonical formatter: formatINR(paise) - Use this for all new code.
 * formatPaise is an alias for backward compatibility.
 */

/**
 * Format paise to Indian Rupee string with lakh/crore grouping.
 * 
 * This is the canonical formatter for all monetary display.
 * Use this function for all new code.
 * 
 * @param paise - Amount in paise (1 rupee = 100 paise)
 * @returns Formatted string like "₹1,234.56" or "₹1,00,000.00"
 * 
 * @example
 * formatINR(123456)    // "₹1,234.56"
 * formatINR(10000000)  // "₹1,00,000.00"
 * formatINR(-500)      // "-₹5.00"
 */
export function formatINR(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) {
    return '₹0.00';
  }

  const negative = paise < 0;
  const absPaise = Math.abs(paise);
  
  const rupees = Math.floor(absPaise / 100);
  const paisePart = absPaise % 100;
  
  // Format with Indian grouping (lakhs, crores)
  let formatted: string;
  if (rupees <= 999) {
    formatted = rupees.toString();
  } else {
    const s = rupees.toString();
    const last3 = s.slice(-3);
    const remaining = s.slice(0, -3);
    const groups: string[] = [];
    
    let r = remaining;
    while (r) {
      groups.push(r.length >= 2 ? r.slice(-2) : r);
      r = r.slice(0, -2);
    }
    groups.reverse();
    formatted = groups.join(',') + ',' + last3;
  }
  
  const result = `₹${formatted}.${paisePart.toString().padStart(2, '0')}`;
  return negative ? `-${result}` : result;
}

/**
 * Format paise to Indian Rupee string with lakh/crore grouping.
 * 
 * @deprecated Use formatINR instead. This is an alias for backward compatibility.
 * @param paise - Amount in paise (1 rupee = 100 paise)
 * @returns Formatted string like "₹1,234.56" or "₹1,00,000.00"
 * 
 * @example
 * formatPaise(123456)    // "₹1,234.56"
 * formatPaise(10000000)  // "₹1,00,000.00"
 * formatPaise(-500)      // "-₹5.00"
 */
export function formatPaise(paise: number | null | undefined): string {
  return formatINR(paise);
}


/**
 * Convert rupees (float) to paise (integer).
 * Uses rounding to handle floating-point precision issues.
 * 
 * @param rupees - Amount in rupees (may have decimal)
 * @returns Amount in paise (integer)
 * 
 * @example
 * rupeesToPaise(123.45)  // 12345
 * rupeesToPaise(100)     // 10000
 */
export function rupeesToPaise(rupees: number): number {
  return Math.round(rupees * 100);
}


/**
 * Convert paise to rupees (float).
 * Note: Prefer using paise for all calculations to avoid precision issues.
 * 
 * @param paise - Amount in paise
 * @returns Amount in rupees (float)
 * 
 * @example
 * paiseToRupees(12345)  // 123.45
 */
export function paiseToRupees(paise: number): number {
  return paise / 100;
}


/**
 * Format a number as percentage with sign.
 * 
 * @param value - The value to format
 * @param decimals - Number of decimal places (default 1)
 * @returns Formatted string like "+15.5%" or "-10.0%"
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}


/**
 * Format a date string to display format.
 * 
 * @param dateStr - Date string in any format
 * @returns Formatted date like "15 Jun 2025"
 */
export function formatDateDisplay(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  
  // Try parsing various formats
  const formats = [
    /^(\d{4})-(\d{2})-(\d{2})$/,           // YYYY-MM-DD
    /^(\d{2})\/(\d{2})\/(\d{4})$/,         // DD/MM/YYYY
    /^(\d{2})-(\d{2})-(\d{4})$/,           // DD-MM-YYYY
  ];
  
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  
  // Try YYYY-MM-DD
  const match1 = dateStr.match(formats[0]);
  if (match1) {
    const [, year, month, day] = match1;
    return `${parseInt(day)} ${months[parseInt(month) - 1]} ${year}`;
  }
  
  // Try DD/MM/YYYY or DD-MM-YYYY
  const match2 = dateStr.match(formats[1]) || dateStr.match(formats[2]);
  if (match2) {
    const [, day, month, year] = match2;
    return `${parseInt(day)} ${months[parseInt(month) - 1]} ${year}`;
  }
  
  return dateStr;
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


/**
 * Truncate text with ellipsis.
 *
 * @param text - Text to truncate
 * @param maxLength - Maximum length (default 30)
 * @returns Truncated text with "..." if needed
 */
export function truncateText(text: string | null | undefined, maxLength: number = 30): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Format a timestamp as a relative time string (e.g., "2m ago", "1h ago").
 */
export function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
