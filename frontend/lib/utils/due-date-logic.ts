/**
 * Smart Amount Due calculation based on current date and bill cycle
 */

export function getAmountDueDisplay(card: {
  totalAmountDue: number;
  dueDate: string;
  billCycleEnd: string;
}): {
  amount: number;
  status: 'due' | 'paid' | 'pending';
  message: string;
} {
  const today = new Date();
  
  // Parse due date
  const dueDate = parseDate(card.dueDate);
  const billCycleEnd = parseDate(card.billCycleEnd);
  
  if (!dueDate || !billCycleEnd) {
    return { amount: 0, status: 'pending', message: 'Date not available' };
  }
  
  // Check if past due date - assume paid
  if (today > dueDate) {
    return { amount: 0, status: 'paid', message: 'Bill paid (assumed)' };
  }
  
  // Check if between bill cycle end and due date - show amount due
  if (today >= billCycleEnd && today <= dueDate) {
    return { 
      amount: card.totalAmountDue, 
      status: 'due', 
      message: `Due by ${formatDate(dueDate)}` 
    };
  }
  
  // Before bill cycle end - bill not yet generated
  return { amount: 0, status: 'pending', message: 'Bill not yet generated' };
}

function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  
  // Try different date formats
  const formats = [
    // DD/MM/YYYY
    /(\d{2})\/(\d{2})\/(\d{4})/,
    // DD-MM-YYYY
    /(\d{2})-(\d{2})-(\d{4})/,
    // DD MMM YYYY
    /(\d{2})\s+([A-Z]{3})\s+(\d{4})/
  ];
  
  for (const format of formats) {
    const match = dateStr.match(format);
    if (match) {
      let day = parseInt(match[1]);
      let month = parseInt(match[2]) - 1; // JS months are 0-indexed
      let year = parseInt(match[3]);
      
      // Handle month names for format 3
      if (match[2].length === 3) {
        const monthNames = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
        month = monthNames.indexOf(match[2].toUpperCase());
      }
      
      const date = new Date(year, month, day);
      if (!isNaN(date.getTime())) {
        return date;
      }
    }
  }
  
  return null;
}

function formatDate(date: Date): string {
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
}

/**
 * Calculate total amount due across all cards with smart logic
 */
export function calculateTotalAmountDue(cards: Array<{
  totalAmountDue: number;
  dueDate: string;
  billCycleEnd: string;
}>): {
  totalDue: number;
  status: 'due' | 'paid' | 'pending';
  message: string;
} {
  let totalDue = 0;
  let hasDue = false;
  let hasPending = false;
  
  for (const card of cards) {
    const display = getAmountDueDisplay(card);
    if (display.status === 'due') {
      totalDue += display.amount;
      hasDue = true;
    } else if (display.status === 'pending') {
      hasPending = true;
    }
  }
  
  if (hasDue) {
    return {
      totalDue,
      status: 'due',
      message: `${cards.length} card(s) have bills due`
    };
  } else if (hasPending) {
    return {
      totalDue: 0,
      status: 'pending',
      message: 'No bills currently due'
    };
  } else {
    return {
      totalDue: 0,
      status: 'paid',
      message: 'All bills paid'
    };
  }
}