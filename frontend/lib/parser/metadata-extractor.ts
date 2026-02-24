/**
 * Proximity-Based Metadata Extractor
 * Version 3.0 - Fixed Total Amount Due patterns
 */

// ==========================================
// CORE PROXIMITY HELPERS
// ==========================================

export function findValueNear(text: string, label: string, type: string = 'currency', maxDistance: number = 200): number | string | null {
    const regex = new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
    const match = text.match(regex);
    
    if (!match) return null;
    
    const startPos = match.index! + match[0].length;
    const searchArea = text.substring(startPos, startPos + maxDistance);
    
    switch(type) {
        case 'currency':
            return extractCurrency(searchArea);
        case 'date':
            return extractDate(searchArea);
        case 'cardNumber':
            return extractCardNumber(searchArea);
        default:
            return null;
    }
}

export function extractCurrency(text: string): number | null {
    const patterns = [
        /(\d{1,2},\d{2},\d{3}\.\d{2})/,
        /(\d{1,3}(?:,\d{3})+\.\d{2})/,
        /(\d{4,}\.\d{2})/,
        /(?:₹|Rs\.?|`)\s*([\d,]+\.\d{2})/i,
        /([\d,]+\.\d{2})\s*(?:Cr|Dr)/i,
        /(\d{3,}(?:,\d{3})*\.\d{2})/
    ];
    
    for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) {
            const value = match[1] || match[0];
            return parseFloat(value.replace(/,/g, ''));
        }
    }
    
    return null;
}

export function extractDate(text: string): string | null {
    const patterns = [
        /(\d{2}\/\d{2}\/\d{4})/,
        /(\d{2}-\d{2}-\d{4})/,
        /(\d{2}\/\w{3}\/\d{4})/i,
        /(\d{2}\s+\w{3}\s+\d{2,4})/i,
        /(\w+\s+\d{1,2},?\s+\d{4})/i
    ];
    
    for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) return match[1];
    }
    
    return null;
}

export function extractCardNumber(text: string): string | null {
    const patterns = [
        /(\d{4}\s*\d{2}XX\s*XXXX\s*\d{4})/i,
        /(\d{6}\*+\d{4})/,
        /(XXXX\s*XXXX\s*XXXX\s*XX\d{2})/i,
        /(\d{4}X{8}\d{4})/,
        /(\d{4}X{4,}\d+)/,
        /(XX\d{4})/
    ];
    
    for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) return match[1];
    }
    
    return null;
}

export function calculateBillCycle(statementDate: string): { billCycleStart: string | null, billCycleEnd: string | null } {
    if (!statementDate) return { billCycleStart: null, billCycleEnd: null };
    
    let endDate: Date | null = null;
    const months3: Record<string, number> = { 
        Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5, 
        Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11 
    };
    const monthsFull: Record<string, number> = { 
        January: 0, February: 1, March: 2, April: 3, May: 4, June: 5,
        July: 6, August: 7, September: 8, October: 9, November: 10, December: 11
    };
    
    let match = statementDate.match(/(\d{2})[\/\-](\d{2})[\/\-](\d{4})/);
    if (match) {
        endDate = new Date(parseInt(match[3]), parseInt(match[2]) - 1, parseInt(match[1]));
    }
    
    if (!endDate) {
        match = statementDate.match(/(\d{2})\s+(\w{3})\s+(\d{2,4})/);
        if (match) {
            const year = match[3].length === 2 ? 2000 + parseInt(match[3]) : parseInt(match[3]);
            const monthIndex = months3[match[2] as keyof typeof months3];
            if (monthIndex !== undefined) {
                endDate = new Date(year, monthIndex, parseInt(match[1]));
            }
        }
    }
    
    if (!endDate) {
        match = statementDate.match(/(\d{2})\/(\w{3})\/(\d{4})/);
        if (match) {
            const monthIndex = months3[match[2] as keyof typeof months3];
            if (monthIndex !== undefined) {
                endDate = new Date(parseInt(match[3]), monthIndex, parseInt(match[1]));
            }
        }
    }

    if (!endDate) {
        match = statementDate.match(/(\w+)\s+(\d{1,2}),?\s+(\d{4})/);
        if (match) {
            const monthIndex = monthsFull[match[1] as keyof typeof monthsFull];
            if (monthIndex !== undefined) {
                endDate = new Date(parseInt(match[3]), monthIndex, parseInt(match[2]));
            }
        }
    }
    
    if (!endDate || isNaN(endDate.getTime())) {
        return { billCycleStart: null, billCycleEnd: null };
    }
    
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - 29);
    
    const formatDate = (d: Date) => {
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        return `${day}/${month}/${year}`;
    };
    
    return {
        billCycleStart: formatDate(startDate),
        billCycleEnd: formatDate(endDate)
    };
}

// ==========================================
// BANK-SPECIFIC CONFIGURATIONS
// ==========================================

interface FieldConfig {
    directPattern?: RegExp;
    extractIndex?: number;
    transform?: (match: string) => string;
    labels?: string[];
    type?: string;
    distance?: number;
    searchAfter?: string;
}

interface BankConfig {
    cardNumber?: FieldConfig;
    totalAmountDue?: FieldConfig;
    minimumAmountDue?: FieldConfig;
    dueDate?: FieldConfig;
    creditLimit?: FieldConfig;
    openingBalance?: FieldConfig;
    billCycle?: {
        pattern: RegExp;
    };
}

export const BANK_METADATA_CONFIG: Record<string, BankConfig> = {
    'HDFC Bank': {
        cardNumber: { 
            labels: ['Card No:', 'Card Number:'], 
            type: 'cardNumber', 
            distance: 50 
        },
        totalAmountDue: { 
            directPattern: /Payment Due Date\s+Total Dues\s+Minimum Amount Due\s+[\d\/]+\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})/i,
            extractIndex: 1
        },
        minimumAmountDue: { 
            directPattern: /Payment Due Date\s+Total Dues\s+Minimum Amount Due\s+[\d\/]+\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})/i,
            extractIndex: 2
        },
        dueDate: { 
            directPattern: /Payment Due Date\s+Total Dues\s+Minimum Amount Due\s+(\d{2}\/\d{2}\/\d{4})/i
        },
        creditLimit: { 
            directPattern: /Credit Limit\s+Available Credit Limit\s+Available Cash Limit\s+([\d,]+)/i
        },
        openingBalance: { 
            directPattern: /Opening\s*Balance[\s\S]*?([\d,]+\.\d{2})/i
        },
        billCycle: { 
            pattern: /Statement Date[:\s]+(\d{2}\/\d{2}\/\d{4})/i 
        }
    },
    
    'Axis Bank': {
        cardNumber: { 
            directPattern: /(\d{6}\*+\d{4})/
        },
        totalAmountDue: { 
            directPattern: /(\d{2}\/\d{2}\/\d{4}\s*-\s*\d{2}\/\d{2}\/\d{4}[\s\S]*?)(\d{1,3}(?:,\d{3})*\.\d{2})\s+Cr\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+Cr/i,
            extractIndex: 2
        },
        minimumAmountDue: { 
            directPattern: /(\d{2}\/\d{2}\/\d{4}\s*-\s*\d{2}\/\d{2}\/\d{4}[\s\S]*?)(\d{1,3}(?:,\d{3})*\.\d{2})\s+Cr\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+Cr/i,
            extractIndex: 3
        },
        dueDate: { 
            directPattern: /(\d{2}\/\d{2}\/\d{4})\s*-\s*\d{2}\/\d{2}\/\d{4}[\s\S]*?(\d{2}\/\d{2}\/\d{4})/i,
            extractIndex: 2
        },
        creditLimit: { 
            directPattern: /Credit Limit[\s\S]*?([\d,]+\.\d{2})/i
        },
        openingBalance: { 
            directPattern: /Previous Balance[\s\S]*?([\d,]+\.\d{2})\s+Dr/i
        },
        billCycle: { 
            pattern: /(\d{2}\/\d{2}\/\d{4})\s*-\s*(\d{2}\/\d{2}\/\d{4})/ 
        }
    },
    
    'ICICI Bank': {
        cardNumber: { 
            directPattern: /(\d{4}X{4,}\d+)/i 
        },
        totalAmountDue: { 
            directPattern: /`\s*[\d,]+\.\d{2}[\s\S]*?`\s*([\d,]+\.\d{2})/i
        },
        minimumAmountDue: { 
            directPattern: /`\s*([\d,]+\.\d{2})/i
        },
        dueDate: { 
            directPattern: /PAYMENT DUE DATE[\s\S]*?(\w+\s+\d{1,2},\s*\d{4})/i
        },
        creditLimit: { 
            directPattern: /Credit Limit[\s\S]*?`\s*(\d{1,2},\d{2},\d{3}\.\d{2})/i
        },
        openingBalance: { 
            directPattern: /Previous Balance[\s\S]*?`\s*([\d,]+\.\d{2})/i
        },
        billCycle: { 
            pattern: /STATEMENT DATE[\s\S]*?(\w+\s+\d{1,2},\s*\d{4})/i 
        }
    },
    
    'SBI Card': {
        cardNumber: { 
            directPattern: /XXXX XXXX XXXX XX(\d{2})/i, 
            transform: (m: string) => 'XXXX XXXX XXXX XX' + m 
        },
        totalAmountDue: { 
            directPattern: /CKYC No[\s\S]*?:\s*\d+\s+([\d,]+\.\d{2})/i
        },
        minimumAmountDue: { 
            directPattern: /CKYC No[\s\S]*?:\s*\d+\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})/i
        },
        dueDate: { 
            directPattern: /(\d{2}\s+\w{3}\s+\d{4})\s+(\d{2}\s+\w{3}\s+\d{4})/i,
            extractIndex: 2
        },
        creditLimit: { 
            directPattern: /(\d{1,2},\d{2},\d{3}\.\d{2})\s+[\d,]+\.\d{2}/i
        },
        openingBalance: { 
            directPattern: /[\d,]+\.\d{2}\s+([\d,]+\.\d{2})/i,
            searchAfter: 'CKYC'
        },
        billCycle: { 
            pattern: /for Statement Period:\s*(\d{1,2}\s+\w{3}\s+\d{2})\s+to\s+(\d{1,2}\s+\w{3}\s+\d{2})/i 
        }
    },
    
    'IDFC First Bank': {
        cardNumber: { 
            directPattern: /FIRST\s+\w+\+?\s+(XX\d{4})/i 
        },
        totalAmountDue: { 
            directPattern: /Total Amount Due[\s\S]*?r\s*([\d,]+\.\d{2})\s*DR/i
        },
        minimumAmountDue: { 
            directPattern: /Minimum Amount Due[\s\S]*?r\s*([\d,]+\.\d{2})/i
        },
        dueDate: { 
            directPattern: /Payment Due Date[\s\S]*?(\d{2}\/\w{3}\/\d{4})/i
        },
        creditLimit: { 
            directPattern: /Credit Limit[\s\S]*?r\s*([\d,]+)/i
        },
        openingBalance: { 
            directPattern: /Opening Balance[\s\S]*?r\s*([\d,]+\.\d{2})/i
        },
        billCycle: { 
            pattern: /(\d{2}\/\w{3}\/\d{4})\s*-\s*(\d{2}\/\w{3}\/\d{4})/i 
        }
    },
    
    'IndusInd Bank': {
        cardNumber: { 
            directPattern: /(\d{4}X{8}\d{4})/ 
        },
        totalAmountDue: { 
            directPattern: /Credit\s*\n\s*Summary[\s\S]*?(\d{5,}\.\d{2})\s*DR/i
        },
        minimumAmountDue: { 
            directPattern: /Credit\s*\n\s*Summary[\s\S]*?\d{5,}\.\d{2}\s*DR[\s\S]*?(\d{5,}\.\d{2})/i
        },
        dueDate: { 
            directPattern: /(\d{2}\/\d{2}\/\d{4})[\s\S]*?\d{2}\/\d{2}\/\d{4}\s*To/i
        },
        creditLimit: { 
            directPattern: /Credit Limit\s+Available Credit Limit[\s\S]*?(\d{6,}\.?\d*)/i
        },
        openingBalance: { 
            directPattern: /(\d{5,}\.\d{2})\s*DR\s*\n/i
        },
        billCycle: { 
            pattern: /(\d{2}\/\d{2}\/\d{4})\s*To\s*(\d{2}\/\d{2}\/\d{4})/i 
        }
    }
};

// ==========================================
// MAIN EXTRACTOR
// ==========================================

export interface Metadata {
    bankName: string;
    cardNumber: string | null;
    cardType: string | null;
    openingBalance: number;
    creditLimit: number;
    totalAmountDue: number;
    minimumAmountDue: number;
    dueDate: string | null;
    billCycleStart: string | null;
    billCycleEnd: string | null;
}

export function extractCreditCardMetadata(text: string, bankName: string): Metadata {
    const config = BANK_METADATA_CONFIG[bankName];
    
    if (!config) {
        console.warn(`No configuration for bank: ${bankName}`);
        return createEmptyMetadata(bankName);
    }
    
    const metadata: Metadata = {
        bankName,
        cardNumber: null,
        cardType: null,
        openingBalance: 0,
        creditLimit: 0,
        totalAmountDue: 0,
        minimumAmountDue: 0,
        dueDate: null,
        billCycleStart: null,
        billCycleEnd: null
    };
    
    for (const [field, fieldConfig] of Object.entries(config)) {
        if (field === 'billCycle') {
            const match = text.match(fieldConfig.pattern);
            if (match) {
                if (match[2]) {
                    metadata.billCycleStart = match[1];
                    metadata.billCycleEnd = match[2];
                } else {
                    const cycle = calculateBillCycle(match[1]);
                    metadata.billCycleStart = cycle.billCycleStart;
                    metadata.billCycleEnd = cycle.billCycleEnd;
                }
            }
            continue;
        }
        
        let value: number | string | null = null;
        
        if (fieldConfig.directPattern) {
            const match = text.match(fieldConfig.directPattern);
            if (match) {
                const idx = fieldConfig.extractIndex || 1;
                let extracted = match[idx] || match[1] || match[0];
                
                if (fieldConfig.transform) {
                    extracted = fieldConfig.transform(extracted);
                }
                
                if (['totalAmountDue', 'minimumAmountDue', 'openingBalance', 'creditLimit'].includes(field)) {
                    value = parseFloat(extracted.replace(/,/g, ''));
                } else {
                    value = extracted;
                }
            }
        }
        
        if (value === null && fieldConfig.labels) {
            for (const label of fieldConfig.labels) {
                value = findValueNear(text, label, fieldConfig.type, fieldConfig.distance || 200);
                if (value) break;
            }
        }
        
        if (value !== null && !isNaN(Number(value))) {
            const numericValue = Number(value);
            switch (field) {
                case 'creditLimit':
                    metadata.creditLimit = numericValue;
                    break;
                case 'totalAmountDue':
                    metadata.totalAmountDue = numericValue;
                    break;
                case 'minimumAmountDue':
                    metadata.minimumAmountDue = numericValue;
                    break;
                case 'openingBalance':
                    metadata.openingBalance = numericValue;
                    break;
                case 'cardNumber':
                    metadata.cardNumber = String(value);
                    break;
                case 'dueDate':
                    metadata.dueDate = String(value);
                    break;
            }
        } else if (value !== null && typeof value === 'string') {
            switch (field) {
                case 'cardNumber':
                    metadata.cardNumber = value;
                    break;
                case 'dueDate':
                    metadata.dueDate = value;
                    break;
            }
        }
    }
    
    return metadata;
}

function createEmptyMetadata(bankName: string): Metadata {
    return {
        bankName,
        cardNumber: null,
        cardType: null,
        openingBalance: 0,
        creditLimit: 0,
        totalAmountDue: 0,
        minimumAmountDue: 0,
        dueDate: null,
        billCycleStart: null,
        billCycleEnd: null
    };
}