/**
 * Formatting Utilities
 * 
 * Phase 2A: Functions for formatting paise values to display strings.
 * All financial calculations should use paise (INTEGER), display uses formatted strings.
 */

/**
 * Format paise to Indian Rupee string with lakh/crore grouping.
 * 
 * @param paise - Amount in paise (1 rupee = 100 paise)
 * @returns Formatted string like "₹1,234.56" or "₹1,00,000.00"
 * 
 * @example
 * formatPaise(123456)    // "₹1,234.56"
 * formatPaise(10000000)  // "₹1,00,000.00"
 * formatPaise(-500)      // "-₹5.00"
 */
export function formatPaise(paise: number | null | undefined): string {
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
  
  // Define regex patterns with non-null assertion (they are literal patterns)
  const format1 = /^(\d{4})-(\d{2})-(\d{2})$/;           // YYYY-MM-DD
  const format2 = /^(\d{2})\/(\d{2})\/(\d{4})$/;         // DD/MM/YYYY
  const format3 = /^(\d{2})-(\d{2})-(\d{4})$/;           // DD-MM-YYYY
  
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  
  // Try YYYY-MM-DD
  const match1 = dateStr.match(format1);
  if (match1) {
    const year = match1[1]!;
    const month = match1[2]!;
    const day = match1[3]!;
    return `${parseInt(day)} ${months[parseInt(month) - 1]} ${year}`;
  }
  
  // Try DD/MM/YYYY
  const match2 = dateStr.match(format2);
  if (match2) {
    const day = match2[1]!;
    const month = match2[2]!;
    const year = match2[3]!;
    return `${parseInt(day)} ${months[parseInt(month) - 1]} ${year}`;
  }
  
  // Try DD-MM-YYYY
  const match3 = dateStr.match(format3);
  if (match3) {
    const day = match3[1]!;
    const month = match3[2]!;
    const year = match3[3]!;
    return `${parseInt(day)} ${months[parseInt(month) - 1]} ${year}`;
  }
  
  return dateStr;
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
 * Format paise to INR compact format (₹1.2K, ₹3.5L).
 * 
 * @param paise - Amount in paise
 * @returns Compact formatted string like "₹1.2K" or "₹3.5L"
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
 * Format paise to Indian Rupee string.
 * 
 * @param paise - Amount in paise
 * @returns Formatted string like "₹1,234" or "₹1,00,000"
 */
export function formatINR(paise: number | null | undefined): string {
  if (paise === null || paise === undefined) return '—';
  const rupees = paise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(rupees);
}

/**
 * Format percentage value with sign.
 * 
 * @param value - Percentage value
 * @returns Formatted string like "+5.2%" or "-10.0%"
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
}

/**
 * Format months to human-readable string.
 * 
 * @param months - Number of months
 * @returns Formatted string like "2y 6m" or "3m"
 */
export function formatMonths(months: number | null | undefined): string {
  if (months === null || months === undefined) return '—';
  if (months >= 12) return `${Math.floor(months / 12)}y ${months % 12}m`;
  return `${months}m`;
}

/**
 * Format date to display format.
 * 
 * @param dateStr - Date string or Date object
 * @returns Formatted date like "15 Jun 2025"
 */
export function formatDate(dateStr: string | Date | null | undefined): string {
  if (!dateStr) return '';
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
  return date.toLocaleDateString('en-IN', { 
    day: 'numeric', 
    month: 'short', 
    year: 'numeric' 
  });
}

/**
 * Format account type for display.
 * 
 * @param type - Account type string
 * @returns Formatted account type
 */
export function formatAccountType(type: string): string {
  const types: Record<string, string> = {
    savings: 'Savings',
    current: 'Current',
    fd: 'Fixed Deposit',
    rd: 'Recurring Deposit',
    wallet: 'Wallet',
    credit_card: 'Credit Card',
  };
  return types[type] || type;
}

/**
 * Get color class for account type.
 * 
 * @param type - Account type string
 * @returns Tailwind color classes
 */
export function getAccountTypeColor(type: string): string {
  const colors: Record<string, string> = {
    savings: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
    current: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
    fd: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
    rd: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
    wallet: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-300',
    credit_card: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  };
  return colors[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/40 dark:text-gray-300';
}

/**
 * Format card type for display.
 * 
 * @param type - Card type string
 * @returns Formatted card type
 */
export function formatCardType(type: string): string {
  const types: Record<string, string> = {
    visa: 'Visa',
    mastercard: 'Mastercard',
    rupay: 'RuPay',
    amex: 'American Express',
    diners: 'Diners Club',
  };
  return types[type] || type;
}