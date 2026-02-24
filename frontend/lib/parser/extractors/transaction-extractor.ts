/**
 * Transaction Extraction
 * Uses table detection first, falls back to regex patterns
 */
import type { DocumentData } from '../core/text-extractor';
import { detectTransactionTable, extractTransactionsFromTable } from '../semantic/table-detector';
import type { Transaction } from '@/types/transaction';

// Regex patterns for transaction extraction (fallback)
const TRANSACTION_PATTERNS = [
    // HDFC: DD/MM/YYYY HH:MM:SS Description Amount [Cr]
    {
        regex: /^(\d{2}\/\d{2}\/\d{4})\s+\d{2}:\d{2}:\d{2}\s+([A-Za-z][A-Za-z0-9\s\*\/\-\.\,\(\)\*#@%&]{5,}?)\s+([\d,]+\.\d{2})(?:\s*(Cr))?\s*$/gm,
        dateIndex: 1, descIndex: 2, amountIndex: 3, typeIndex: 4
    },
    // SBI: DD Mon YY Description Amount C/D
    {
        regex: /(\d{2}\s+[A-Za-z]{3}\s+\d{2})\s+([A-Za-z#\*][A-Za-z0-9\s\/\-\.\,\(\)\*#@%&]+?)\s+([\d,]+\.\d{2})\s*([CDM])\s*$/gm,
        dateIndex: 1, descIndex: 2, amountIndex: 3, typeIndex: 4
    },
    // IDFC: DD Mon YY Description Amount DR/CR
    {
        regex: /(\d{2}\s+[A-Za-z]{3}\s+\d{2})\s+([A-Za-z][A-Za-z0-9\s\/\-\.,\(\)]+?)\s+([\d,]+\.\d{2})\s*(DR|CR)\s*$/gim,
        dateIndex: 1, descIndex: 2, amountIndex: 3, typeIndex: 4
    },
    // ICICI: DD/MM/YYYY Description Amount [CR]
    {
        regex: /(\d{2}\/\d{2}\/\d{4})\s+([A-Za-z][A-Za-z\s\*\/\-\.<>@%\(\)]{5,}?)\s+([\d,]+\.\d{2})\s*(CR)?/gim,
        dateIndex: 1, descIndex: 2, amountIndex: 3, typeIndex: 4
    },
    // Generic: DD/MM/YYYY Description Amount [Dr/Cr]
    {
        regex: /(\d{2}\/\d{2}\/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s*(Dr|Cr)?/gi,
        dateIndex: 1, descIndex: 2, amountIndex: 3, typeIndex: 4
    }
];

/**
 * Extract transactions from document
 * First tries table detection, falls back to regex
 */
export function extractTransactions(documentData: DocumentData, bankName: string): Transaction[] {
    console.log('[TRANSACTIONS] Extracting transactions...');
    
    // Try table detection first (most accurate)
    for (const page of documentData.pages) {
        const table = detectTransactionTable(page);
        if (table && table.rows.length > 0) {
            console.log(`[TRANSACTIONS] Table detected on page ${page.pageNumber}`);
            const rawTransactions = extractTransactionsFromTable(table, bankName);
            
            if (rawTransactions.length > 0) {
                return rawTransactions.map((t, index) => ({
                    id: `txn-${Date.now()}-${index}`,
                    date: normalizeDate(t.date),
                    description: cleanDescription(t.description),
                    amount: t.amount,
                    type: t.type as 'debit' | 'credit',
                    category: categorizeTransaction(t.description),
                    bank: bankName,
                    cardId: ''
                }));
            }
        }
    }
    
    // Fallback to regex patterns
    console.log('[TRANSACTIONS] No table found, using regex fallback');
    return extractWithRegex(documentData.fullText, bankName);
}

/**
 * Extract transactions using regex patterns
 */
function extractWithRegex(text: string, bankName: string): Transaction[] {
    const transactions: Transaction[] = [];
    const seen = new Set<string>();
    
    for (const pattern of TRANSACTION_PATTERNS) {
        const regex = new RegExp(pattern.regex.source, pattern.regex.flags);
        let match;
        
        while ((match = regex.exec(text)) !== null) {
            const date = normalizeDate(match[pattern.dateIndex]);
            const description = cleanDescription(match[pattern.descIndex]);
            const amount = parseFloat(match[pattern.amountIndex].replace(/[^0-9.]/g, ''));
            const typeIndicator = pattern.typeIndex ? match[pattern.typeIndex] : null;
            const type = determineType(typeIndicator, description);
            
            // Skip invalid transactions
            if (!date || !description || isNaN(amount) || amount === 0) continue;
            if (amount > 1000000) continue; // Sanity check
            
            // Deduplicate
            const key = `${date}-${description.substring(0, 30)}-${amount}`;
            if (seen.has(key)) continue;
            seen.add(key);
            
            transactions.push({
                id: `txn-${Date.now()}-${transactions.length}`,
                date,
                description,
                amount,
                type,
                category: categorizeTransaction(description),
                bank: bankName,
                cardId: ''
            });
        }
    }
    
    // Sort by date
    transactions.sort((a, b) => {
        const dateA = a.date.split('/').reverse().join('');
        const dateB = b.date.split('/').reverse().join('');
        return dateA.localeCompare(dateB);
    });
    
    console.log(`[TRANSACTIONS] Extracted ${transactions.length} transactions via regex`);
    return transactions;
}

/**
 * Normalize date to DD/MM/YYYY format
 */
function normalizeDate(dateStr: string): string {
    if (!dateStr) return '';
    
    // Already in DD/MM/YYYY format
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) return dateStr;
    
    // DD-MM-YYYY
    if (/^\d{2}-\d{2}-\d{4}$/.test(dateStr)) {
        return dateStr.replace(/-/g, '/');
    }
    
    // DD Mon YY or DD Mon YYYY
    const monthMatch = dateStr.match(/^(\d{2})\s+(\w{3})\s+(\d{2,4})$/);
    if (monthMatch) {
        const months: Record<string, string> = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        };
        const day = monthMatch[1];
        const month = months[monthMatch[2].toLowerCase()] || '01';
        const year = monthMatch[3].length === 2 ? '20' + monthMatch[3] : monthMatch[3];
        return `${day}/${month}/${year}`;
    }
    
    return dateStr;
}

/**
 * Clean description text
 */
function cleanDescription(desc: string): string {
    return desc
        .replace(/\s+/g, ' ')
        .replace(/[\r\n\t]/g, ' ')
        .trim();
}

/**
 * Determine transaction type (debit/credit)
 */
function determineType(typeIndicator: string | null, description: string): 'debit' | 'credit' {
    if (typeIndicator) {
        const lower = typeIndicator.toLowerCase();
        if (lower === 'c' || lower === 'cr' || lower === 'credit') return 'credit';
        if (lower === 'd' || lower === 'dr' || lower === 'debit' || lower === 'm') return 'debit';
    }
    
    // Check description for credit keywords
    const creditKeywords = ['refund', 'cashback', 'reversal', 'credit', 'received', 'reward', 'payment received'];
    const descLower = description.toLowerCase();
    for (const keyword of creditKeywords) {
        if (descLower.includes(keyword)) return 'credit';
    }
    
    return 'debit';
}

/**
 * Categorize transaction based on description
 */
function categorizeTransaction(description: string): string {
    const desc = description.toLowerCase();
    
    if (desc.includes('swiggy') || desc.includes('zomato') || desc.includes('restaurant') || 
        desc.includes('food') || desc.includes('dining') || desc.includes('cafe')) {
        return 'Food & Dining';
    }
    
    if (desc.includes('amazon') || desc.includes('flipkart') || desc.includes('myntra') || 
        desc.includes('shopping') || desc.includes('retail') || desc.includes('store')) {
        return 'Shopping';
    }
    
    if (desc.includes('uber') || desc.includes('ola') || desc.includes('fuel') || 
        desc.includes('petrol') || desc.includes('diesel') || desc.includes('travel')) {
        return 'Transportation';
    }
    
    if (desc.includes('electricity') || desc.includes('water') || desc.includes('gas') || 
        desc.includes('bill') || desc.includes('recharge') || desc.includes('mobile')) {
        return 'Bills & Utilities';
    }
    
    if (desc.includes('netflix') || desc.includes('prime') || desc.includes('hotstar') || 
        desc.includes('spotify') || desc.includes('movie') || desc.includes('entertainment')) {
        return 'Entertainment';
    }
    
    if (desc.includes('hospital') || desc.includes('pharmacy') || desc.includes('medical') || 
        desc.includes('doctor') || desc.includes('health')) {
        return 'Healthcare';
    }
    
    if (desc.includes('school') || desc.includes('college') || desc.includes('university') || 
        desc.includes('course') || desc.includes('education')) {
        return 'Education';
    }
    
    if (desc.includes('grocery') || desc.includes('supermarket') || desc.includes('bigbasket')) {
        return 'Groceries';
    }
    
    if (desc.includes('credit card') || desc.includes('card payment') || desc.includes('billdesk') || 
        desc.includes('bbps') || desc.includes('payment received')) {
        return 'Credit Card Payment';
    }
    
    if (desc.includes('transfer') || desc.includes('upi') || desc.includes('neft')) {
        return 'Transfer';
    }
    
    if (desc.includes('atm') || desc.includes('cash') || desc.includes('withdrawal')) {
        return 'Cash Withdrawal';
    }
    
    return 'Other';
}
