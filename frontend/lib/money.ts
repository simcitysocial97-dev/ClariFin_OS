/**
 * Money Type and Formatting Utilities
 *
 * Money type matching backend MoneyDTO domain object.
 * All monetary values in the system are represented as integer paise.
 */

/**
 * Money type matching backend MoneyDTO
 */
export interface Money {
  paise: number;  // Total paise (e.g., 123456 = ₹1,234.56)
  rupees: number;  // Derived rupees value for display
}

/**
 * Format Money object as rupees with proper locale formatting
 * @param money - Money object from API
 * @returns Formatted string like "₹1,234.56"
 */
export function formatMoney(money: Money | null | undefined): string {
  if (!money || money.paise === null || money.paise === undefined) {
    return '₹0.00';
  }

  const rupees = money.paise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(rupees);
}

/**
 * Create Money object from rupees (for form inputs)
 */
export function rupeesToMoney(rupees: number): Money {
  return { paise: Math.round(rupees * 100), rupees };
}

/**
 * Get rupees as number (for calculations)
 */
export function moneyToRupees(money: Money): number {
  return money.paise / 100;
}