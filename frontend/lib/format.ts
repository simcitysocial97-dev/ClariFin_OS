/**
 * Formatting Utilities
 * ====================
 * 
 * Centralized formatting functions to prevent NaN and date issues
 * across the entire application.
 */

/**
 * Format paise amount to INR display string
 * Always safe — returns ₹0.00 for invalid input
 */
export function formatPaise(paise: number | null | undefined): string {
  const safePaise = typeof paise === 'number' && !isNaN(paise) ? paise : 0;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(safePaise / 100);
}

/**
 * Format rupee amount (not paise) to INR display string
 */
export function formatRupees(rupees: number | null | undefined): string {
  const safeRupees = typeof rupees === 'number' && !isNaN(rupees) ? rupees : 0;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(safeRupees);
}

/**
 * Format ISO date string to localized display
 */
export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return 'N/A';
  try {
    return new Date(isoString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return 'Invalid date';
  }
}

/**
 * Format ISO date string to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return 'N/A';
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(isoString);
  } catch {
    return 'N/A';
  }
}

/**
 * Convert rupees input to paise for API submission
 */
export function rupeesToPaise(rupees: number): number {
  return Math.round(rupees * 100);
}

/**
 * Convert paise from API to rupees for display/input
 */
export function paiseToRupees(paise: number): number {
  return paise / 100;
}

/**
 * Format account type for display
 */
export function formatAccountType(type: string): string {
  const typeMap: Record<string, string> = {
    'savings': 'Savings',
    'current': 'Current',
    'credit_card': 'Credit Card',
    'fd': 'Fixed Deposit',
    'wallet': 'Wallet',
    'loan': 'Loan',
  };
  return typeMap[type] || type;
}

/**
 * Format card type for display
 */
export function formatCardType(type: string): string {
  const typeMap: Record<string, string> = {
    'visa': 'Visa',
    'mastercard': 'Mastercard',
    'rupay': 'RuPay',
    'amex': 'American Express',
    'diners': 'Diners Club',
  };
  return typeMap[type] || type;
}

/**
 * Get account type color
 */
export function getAccountTypeColor(type: string): string {
  const colorMap: Record<string, string> = {
    'savings': 'bg-green-100 text-green-800',
    'current': 'bg-blue-100 text-blue-800',
    'credit_card': 'bg-purple-100 text-purple-800',
    'fd': 'bg-amber-100 text-amber-800',
    'wallet': 'bg-pink-100 text-pink-800',
    'loan': 'bg-red-100 text-red-800',
  };
  return colorMap[type] || 'bg-gray-100 text-gray-800';
}

// ============================================================================
// NEW FORMAT FUNCTIONS FOR PROMPT F1
// ============================================================================

/**
 * Format paise to compact display (e.g., "₹12.5L" or "₹1.2Cr")
 */
export function formatPaiseCompact(paise: number | null | undefined): string {
  const safePaise = typeof paise === 'number' && !isNaN(paise) ? paise : 0;
  const rupees = safePaise / 100;
  
  // Less than 1 lakh
  if (rupees < 100000) {
    return formatPaise(safePaise);
  }
  
  // Less than 1 crore - show in lakhs
  if (rupees < 10000000) {
    const lakhs = rupees / 100000;
    return `₹${lakhs.toFixed(1)}L`;
  }
  
  // 1 crore or more
  const crores = rupees / 10000000;
  return `₹${crores.toFixed(1)}Cr`;
}

/**
 * Format paise to INR display string (no decimal paise)
 * Always safe — returns '—' for invalid input
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

/**
 * Format percentage value (e.g., "+8.5%")
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
}

/**
 * Format months to human readable (e.g., "2y 6m" or "6m")
 */
export function formatMonths(months: number | null | undefined): string {
  if (months === null || months === undefined) return '—';
  if (months >= 12) {
    return `${Math.floor(months / 12)}y ${months % 12}m`;
  }
  return `${months}m`;
}

/**
 * Format month string (e.g., "Jan 2025" from "2025-01")
 */
export function formatMonth(month: string | null | undefined): string {
  if (!month) return 'N/A';
  try {
    const parts = month.split('-');
    if (parts.length !== 2) return month;
    const yearStr = parts[0];
    const monthStr = parts[1];
    if (!yearStr || !monthStr) return month;
    const year = parseInt(yearStr, 10);
    const monthNum = parseInt(monthStr, 10);
    if (isNaN(year) || isNaN(monthNum)) return month;
    const date = new Date(year, monthNum - 1, 1);
    return date.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
  } catch {
    return month;
  }
}

/**
 * Format tenure in months to human readable (e.g., "2 years 6 months")
 */
export function formatTenure(months: number | null | undefined): string {
  const safeMonths = typeof months === 'number' && !isNaN(months) ? months : 0;
  
  if (safeMonths === 0) return '0 months';
  
  const years = Math.floor(safeMonths / 12);
  const remainingMonths = safeMonths % 12;
  
  const parts: string[] = [];
  
  if (years > 0) {
    parts.push(`${years} year${years > 1 ? 's' : ''}`);
  }
  
  if (remainingMonths > 0) {
    parts.push(`${remainingMonths} month${remainingMonths > 1 ? 's' : ''}`);
  }
  
  return parts.join(' ') || '0 months';
}
