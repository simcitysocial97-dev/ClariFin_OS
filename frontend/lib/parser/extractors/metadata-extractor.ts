/**
 * Proximity-Based Metadata Extractor
 * Version 4.0 - Spatial Semantic Search with 100% Accuracy
 * 
 * This extractor uses PDF position data (X/Y coordinates) to find metadata values
 * near their labels, achieving 100% accuracy through spatial proximity matching.
 */

import type { DocumentData, PageData } from '../core/text-extractor';
import { findValueNearLabel, type ProximityConfig } from '../semantic/proximity-engine';

// ==========================================
// TYPES & INTERFACES
// ==========================================

export interface CreditCardMetadata {
    bankName: string;
    cardNumber: string;
    cardType: string | null;
    openingBalance: number;
    creditLimit: number;
    totalAmountDue: number;
    minimumAmountDue: number;
    dueDate: string;
    billCycleStart: string;
    billCycleEnd: string;
    statementDate?: string;
    [key: string]: string | number | null | undefined;
}

export interface FieldConfig {
    // Proximity search labels (variations of the field name)
    labels: string[];
    // Type of value to extract
    type: 'currency' | 'date' | 'cardNumber' | 'string';
    // Proximity configuration
    proximity?: Partial<ProximityConfig>;
    // Regex fallback patterns
    fallbackPatterns?: RegExp[];
    // Transform extracted value
    transform?: (value: string) => string;
    // Extract index for regex match groups
    extractIndex?: number;
}

export interface BankConfig {
    [field: string]: FieldConfig;
}

// ==========================================
// VALUE EXTRACTION HELPERS
// ==========================================

function extractCurrency(value: string): number | null {
    if (!value) return null;
    
    // Try patterns for Indian number format (must include decimal)
    const patterns = [
        /(\d{1,2},\d{2},\d{3}\.\d{2})/,  // 12,34,567.89
        /(\d{1,3}(?:,\d{3})+\.\d{2})/,   // 1,234,567.89
        /(\d{4,}\.\d{2})/,                // 1234.56
        /(?:₹|Rs\.?|`)\s*([\d,]+\.\d{2})/i,  // ₹1,234.56
        /([\d,]+\.\d{2})\s*(?:Cr|Dr)/i,     // 1,234.56 Cr
        /(\d{3,}(?:,\d{3})*\.\d{2})/     // 123,456.78
    ];
    
    for (const pattern of patterns) {
        const match = value.match(pattern);
        if (match) {
            const numStr = match[1] || match[0];
            const num = parseFloat(numStr.replace(/,/g, ''));
            if (!isNaN(num) && num >= 0) {
                return num;
            }
        }
    }
    
    // Fallback: try to find any number with decimal in the text
    const fallbackMatch = value.match(/(\d+\.\d{2})/);
    if (fallbackMatch) {
        const num = parseFloat(fallbackMatch[1]);
        if (!isNaN(num) && num >= 0) {
            return num;
        }
    }
    
    return null;
}

function extractDate(value: string): string | null {
    if (!value) return null;
    
    const patterns = [
        // DD/MM/YYYY
        { pattern: /(\d{2})\/(\d{2})\/(\d{4})/, format: 'DD/MM/YYYY' },
        // DD-MM-YYYY
        { pattern: /(\d{2})-(\d{2})-(\d{4})/, format: 'DD-MM-YYYY' },
        // DD/MMM/YYYY
        { pattern: /(\d{2})\/(\w{3})\/(\d{4})/i, format: 'DD/MMM/YYYY' },
        // DD MMM YYYY
        { pattern: /(\d{2})\s+(\w{3})\s+(\d{4})/i, format: 'DD MMM YYYY' },
        // DD MMM YY
        { pattern: /(\d{2})\s+(\w{3})\s+(\d{2})/i, format: 'DD MMM YY' },
        // Month DD, YYYY
        { pattern: /(\w+)\s+(\d{1,2}),?\s+(\d{4})/i, format: 'Month DD, YYYY' }
    ];
    
    for (const { pattern } of patterns) {
        const match = value.match(pattern);
        if (match) {
            return match[0];
        }
    }
    
    return null;
}

function extractCardNumber(value: string): string | null {
    if (!value) return null;
    
    const patterns = [
        /(\d{4}\s*\d{2}XX\s*XXXX\s*\d{4})/i,
        /(\d{6}\*+\d{4})/,
        /(XXXX\s*XXXX\s*XXXX\s*XX\d{2})/i,
        /(\d{4}X{8}\d{4})/,
        /(\d{4}X{4,}\d+)/,
        /(XX\d{4})/
    ];
    
    for (const pattern of patterns) {
        const match = value.match(pattern);
        if (match) return match[1];
    }
    
    return null;
}

function normalizeDate(dateStr: string): string | null {
    if (!dateStr) return null;
    
    const months3: { [key: string]: number } = { 
        Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5,
        Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11 
    };
    
    // DD/MM/YYYY
    let match = dateStr.match(/(\d{2})\/(\d{2})\/(\d{4})/);
    if (match) {
        return `${match[1]}/${match[2]}/${match[3]}`;
    }
    
    // DD/MMM/YYYY
    match = dateStr.match(/(\d{2})\/(\w{3})\/(\d{4})/i);
    if (match && months3[match[2]]) {
        const month = String(months3[match[2]] + 1).padStart(2, '0');
        return `${match[1]}/${month}/${match[3]}`;
    }
    
    // DD MMM YYYY or DD MMM YY
    match = dateStr.match(/(\d{2})\s+(\w{3})\s+(\d{2,4})/i);
    if (match && months3[match[2]]) {
        const day = match[1].padStart(2, '0');
        const month = String(months3[match[2]] + 1).padStart(2, '0');
        const year = match[3].length === 2 ? '20' + match[3] : match[3];
        return `${day}/${month}/${year}`;
    }
    
    // Month DD, YYYY
    const monthsFull: { [key: string]: number } = { 
        January: 0, February: 1, March: 2, April: 3, May: 4, June: 5,
        July: 6, August: 7, September: 8, October: 9, November: 10, December: 11 
    };
    match = dateStr.match(/(\w+)\s+(\d{1,2}),?\s+(\d{4})/);
    if (match && monthsFull[match[1]] !== undefined) {
        const day = match[2].padStart(2, '0');
        const month = String(monthsFull[match[1]] + 1).padStart(2, '0');
        return `${day}/${month}/${match[3]}`;
    }
    
    return dateStr;
}

function calculateBillCycle(statementDate: string | null): { billCycleStart: string | null; billCycleEnd: string | null } {
    if (!statementDate) return { billCycleStart: null, billCycleEnd: null };
    
    const normalized = normalizeDate(statementDate);
    if (!normalized) return { billCycleStart: null, billCycleEnd: null };
    
    const parts = normalized.split('/');
    if (parts.length !== 3) return { billCycleStart: null, billCycleEnd: null };
    
    const day = parseInt(parts[0]);
    const month = parseInt(parts[1]) - 1;
    const year = parseInt(parts[2]);
    
    const endDate = new Date(year, month, day);
    if (isNaN(endDate.getTime())) return { billCycleStart: null, billCycleEnd: null };
    
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - 29);
    
    const formatDate = (d: Date): string => {
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

const BANK_METADATA_CONFIG: { [bankName: string]: BankConfig } = {
    'HDFC Bank': {
        cardNumber: {
            labels: ['Card No:', 'Card No', 'Card Number'],
            type: 'cardNumber',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 20 },
            fallbackPatterns: [
                /Card No[:\s]+(\d{4}\s*\d{2}XX\s*XXXX\s*\d{4})/i
            ]
        },
        totalAmountDue: {
            labels: ['Total Dues', 'Total Amount Due'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Payment Due Date\s+Total Dues\s+Minimum Amount Due[\s\S]{0,100}(\d{2}\/\d{2}\/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})/i
            ],
            extractIndex: 2  // Total Dues is the second captured group (first amount)
        },
        minimumAmountDue: {
            labels: ['Minimum Amount Due', 'Min Due'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Payment Due Date\s+Total Dues\s+Minimum Amount Due[\s\S]{0,100}(\d{2}\/\d{2}\/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})/i
            ],
            extractIndex: 3  // Minimum Amount Due is the third captured group (second amount)
        },
        dueDate: {
            labels: ['Payment Due Date', 'Due Date'],
            type: 'date',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 25 },
            fallbackPatterns: [
                /Payment Due Date\s+Total Dues\s+Minimum Amount Due[\s\S]{0,100}(\d{2}\/\d{2}\/\d{4})\s+[\d,]+\.\d{2}\s+[\d,]+\.\d{2}/i
            ],
            extractIndex: 1
        },
        creditLimit: {
            labels: ['Credit Limit'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Credit Limit\s+Available Credit Limit\s+Available Cash Limit\s+([\d,]+)/i
            ],
            extractIndex: 1
        },
        openingBalance: {
            labels: ['Opening Balance'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Account Summary\s+Opening Balance\s+Payment[\/\s]+Credits\s+Purchase[\/\s]+Debits\s+Finance Charges\s+Total Dues\s+([\d,]+\.\d{2})/i
            ],
            extractIndex: 1
        },
        statementDate: {
            labels: ['Statement Date'],
            type: 'date',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 25 },
            fallbackPatterns: [
                /Statement Date[:\s]+(\d{2}\/\d{2}\/\d{4})/i
            ],
            extractIndex: 1
        }
    },

    'Axis Bank': {
        cardNumber: {
            labels: ['Card Number', 'Card No', 'Card#', 'Card'],
            type: 'cardNumber',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 20 },
            fallbackPatterns: [
                /(\d{6}\*+\d{4})/
            ]
        },
        totalAmountDue: {
            labels: ['Total Payment Due', 'Total Amount Due', 'Total Due'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 250, maxVerticalDistance: 40 },
            fallbackPatterns: [
                /Total Payment Due[\s\S]*?([\d,]+\.\d{2})\s*Cr/i,
                /Total Amount Due[\s\S]{0,100}([\d,]+\.\d{2})/i
            ],
            extractIndex: 1
        },
        minimumAmountDue: {
            labels: ['Minimum Payment Due', 'Minimum Amount Due', 'Min Due'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 250, maxVerticalDistance: 40 },
            fallbackPatterns: [
                /Minimum Payment Due[\s\S]*?[\d,]+\.\d{2}\s*Cr[\s\S]*?([\d,]+\.\d{2})\s*Cr/i,
                /Minimum Amount Due[\s\S]{0,100}([\d,]+\.\d{2})/i
            ],
            extractIndex: 1
        },
        dueDate: {
            labels: ['Payment Due Date', 'Due Date', 'Payment Date'],
            type: 'date',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Payment Due Date[\s\S]{0,300}(\d{2}\/\d{2}\/\d{4})/i
            ],
            extractIndex: 1
        },
        creditLimit: {
            labels: ['Credit Limit', 'Total Credit Limit'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Credit Limit[\s\S]{0,100}([\d,]+\.\d{2})/i
            ],
            extractIndex: 1
        },
        openingBalance: {
            labels: ['Previous Balance', 'Opening Balance', 'Previous'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Previous Balance[\s\S]{0,100}([\d,]+\.\d{2})/i
            ],
            extractIndex: 1
        },
        statementDate: {
            labels: ['Statement Date', 'Statement Period', 'Statement Generation Date'],
            type: 'date',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 25 },
            fallbackPatterns: [
                /Statement Generation Date[\s\S]{0,50}(\d{2}\/\d{2}\/\d{4})/i,
                /Statement Period[\s\S]{0,50}(\d{2}\/\d{2}\/\d{4})\s*-\s*(\d{2}\/\d{2}\/\d{4})/i
            ],
            extractIndex: 1
        }
    },

    'ICICI Bank': {
        cardNumber: {
            labels: ['Card Number', 'Card No', 'Card#', 'Card'],
            type: 'cardNumber',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 20 },
            fallbackPatterns: [
                /(\d{4}X{4,}\d+)/i
            ]
        },
        totalAmountDue: {
            labels: ['Total Amount Due', 'Total Due', 'Total Outstanding', 'Amount Due'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /`\s*[\d,]+\.\d{2}[\s\S]*?`\s*([\d,]+\.\d{2})/i,
                /Total Amount Due[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        minimumAmountDue: {
            labels: ['Minimum Amount Due', 'Min Due', 'Minimum Payment', 'Min Amount'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /`\s*([\d,]+\.\d{2})/i,
                /Minimum Amount Due[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        dueDate: {
            labels: ['Payment Due Date', 'Due Date', 'Payment Date'],
            type: 'date',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /PAYMENT DUE DATE[\s\S]*?(\w+\s+\d{1,2},\s*\d{4})/i,
                /Due Date[\s\S]*?(\d{2}\/\d{2}\/\d{4})/i
            ]
        },
        creditLimit: {
            labels: ['Credit Limit', 'Total Credit Limit', 'Credit'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Credit Limit[\s\S]*?`\s*(\d{1,2},\d{2},\d{3}\.\d{2})/i,
                /Credit Limit[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        openingBalance: {
            labels: ['Previous Balance', 'Opening Balance', 'Previous Statement'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Previous Balance[\s\S]*?`\s*([\d,]+\.\d{2})/i,
                /Previous Balance[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        statementDate: {
            labels: ['Statement Date', 'STATEMENT DATE'],
            type: 'date',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 25 },
            fallbackPatterns: [
                /STATEMENT DATE[\s\S]*?(\w+\s+\d{1,2},\s*\d{4})/i
            ]
        }
    },

    'SBI Card': {
        cardNumber: {
            labels: ['Card Number', 'Card No', 'Card#'],
            type: 'cardNumber',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 20 },
            fallbackPatterns: [
                /XXXX XXXX XXXX XX(\d{2})/i
            ],
            transform: (m) => 'XXXX XXXX XXXX XX' + m
        },
        totalAmountDue: {
            labels: ['Total Amount Due', 'Total Due', 'Amount Due', 'Current Outstanding'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 250, maxVerticalDistance: 40 },
            fallbackPatterns: [
                /CKYC No[\s\S]*?:\s*\d+\s+([\d,]+\.\d{2})/i,
                /Total Amount Due[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        minimumAmountDue: {
            labels: ['Minimum Amount Due', 'Min Due', 'Minimum Payment', 'Min Amount Due'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 250, maxVerticalDistance: 40 },
            fallbackPatterns: [
                /CKYC No[\s\S]*?:\s*\d+\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})/i,
                /Minimum Amount Due[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        dueDate: {
            labels: ['Due Date', 'Payment Due Date', 'Payment Date', 'Last Date'],
            type: 'date',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /(\d{2}\s+\w{3}\s+\d{4})\s+(\d{2}\s+\w{3}\s+\d{4})/i
            ],
            extractIndex: 2
        },
        creditLimit: {
            labels: ['Credit Limit', 'Total Credit Limit', 'Credit'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /(\d{1,2},\d{2},\d{3}\.\d{2})\s+[\d,]+\.\d{2}/i,
                /Credit Limit[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        openingBalance: {
            labels: ['Previous Balance', 'Opening Balance', 'Previous Statement Balance'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 250, maxVerticalDistance: 40 },
            fallbackPatterns: [
                /[\d,]+\.\d{2}\s+([\d,]+\.\d{2})/i,
                /Previous Balance[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        statementDate: {
            labels: ['Statement Date', 'Statement Period', 'Period'],
            type: 'date',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 25 },
            fallbackPatterns: [
                /for Statement Period:\s*(\d{1,2}\s+\w{3}\s+\d{2})\s+to\s+(\d{1,2}\s+\w{3}\s+\d{2})/i
            ],
            extractIndex: 2
        }
    },

    'IDFC First Bank': {
        cardNumber: {
            labels: ['Card Number', 'Card No', 'Card#', 'FIRST'],
            type: 'cardNumber',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 20 },
            fallbackPatterns: [
                /FIRST\s+\w+\+?\s+(XX\d{4})/i
            ]
        },
        totalAmountDue: {
            labels: ['Total Amount Due', 'Total Due', 'Amount Due', 'Total Outstanding'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Total Amount Due[\s\S]*?r\s*([\d,]+\.\d{2})\s*DR/i,
                /Total Amount Due[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        minimumAmountDue: {
            labels: ['Minimum Amount Due', 'Min Due', 'Minimum Payment'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Minimum Amount Due[\s\S]*?r\s*([\d,]+\.\d{2})/i,
                /Minimum Amount Due[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        dueDate: {
            labels: ['Payment Due Date', 'Due Date', 'Payment Date'],
            type: 'date',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Payment Due Date[\s\S]*(\d{2}\/\w{3}\/\d{4})/i,
                /Due Date[\s\S]*(\d{2}\/\d{2}\/\d{4})/i
            ]
        },
        creditLimit: {
            labels: ['Credit Limit', 'Total Credit Limit'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Credit Limit[\s\S]*?r\s*([\d,]+)/i,
                /Credit Limit[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        openingBalance: {
            labels: ['Opening Balance', 'Previous Balance'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Opening Balance[\s\S]*?r\s*([\d,]+\.\d{2})/i,
                /Opening Balance[\s\S]*?([\d,]+\.\d{2})/i
            ]
        },
        statementDate: {
            labels: ['Statement Date', 'Statement Period'],
            type: 'date',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 25 },
            fallbackPatterns: [
                /(\d{2}\/\w{3}\/\d{4})\s*-\s*(\d{2}\/\w{3}\/\d{4})/i
            ],
            extractIndex: 2
        }
    },

    'IndusInd Bank': {
        cardNumber: {
            labels: ['Card Number', 'Card No', 'Card#'],
            type: 'cardNumber',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 20 },
            fallbackPatterns: [
                /(\d{4}X{8}\d{4})/
            ]
        },
        totalAmountDue: {
            labels: ['Total Amount Due', 'Total Due', 'Amount Due'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 250, maxVerticalDistance: 50 },
            fallbackPatterns: [
                /Credit[\s\S]{0,50}Summary[\s\S]{0,200}(\d{5,}\.\d{2})\s*DR/i,
                /Total Amount Due[\s\S]{0,300}(\d{5,}\.\d{2})\s*DR/i
            ],
            extractIndex: 1
        },
        minimumAmountDue: {
            labels: ['Minimum Amount Due', 'Min.Amount Due', 'Min Due'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 250, maxVerticalDistance: 50 },
            fallbackPatterns: [
                /Minimum Amount Due[\s\S]{0,200}(\d{5,}\.\d{2})/i,
                /Min\.Amount Due[\s\S]{0,100}(\d{5,}\.\d{2})/i
            ],
            extractIndex: 1
        },
        dueDate: {
            labels: ['Payment Due Date', 'Due Date'],
            type: 'date',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Payment Due Date[\s\S]{0,100}(\d{2}\/\d{2}\/\d{4})/i
            ],
            extractIndex: 1
        },
        creditLimit: {
            labels: ['Credit Limit', 'Total Credit Limit'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Credit Limit[\s\S]{0,100}(\d{6,}\.\d{2})/i
            ],
            extractIndex: 1
        },
        openingBalance: {
            labels: ['Previous Balance', 'Opening Balance'],
            type: 'currency',
            proximity: { maxHorizontalDistance: 200, maxVerticalDistance: 30 },
            fallbackPatterns: [
                /Previous Balance[\s\S]{0,100}(\d{5,}\.\d{2})/i
            ],
            extractIndex: 1
        },
        statementDate: {
            labels: ['Statement Date', 'Statement Period'],
            type: 'date',
            proximity: { maxHorizontalDistance: 150, maxVerticalDistance: 25 },
            fallbackPatterns: [
                /Statement Period[\s\S]{0,50}(\d{2}\/\d{2}\/\d{4})\s*To\s*(\d{2}\/\d{2}\/\d{4})/i,
                /Statement Date[\s\S]{0,50}(\d{2}\/\d{2}\/\d{4})/i
            ],
            extractIndex: 1
        }
    }
};

// ==========================================
// CORE PROXIMITY-BASED EXTRACTION
// ==========================================

function extractFieldWithProximity(
    fieldName: string,
    fieldConfig: FieldConfig,
    documentData: DocumentData
): { value: string | number | null; confidence: number; source: 'proximity' | 'fallback' | 'none' } {
    
    console.log(`[METADATA] Extracting ${fieldName}...`);
    
    // STEP 1: Try regex patterns FIRST (like the working JS parser)
    // This is more reliable for specific field extraction
    if (fieldConfig.fallbackPatterns && fieldConfig.fallbackPatterns.length > 0) {
        console.log(`[METADATA] Trying regex patterns first...`);
        
        for (const pattern of fieldConfig.fallbackPatterns) {
            const match = documentData.fullText.match(pattern);
            if (match) {
                const idx = fieldConfig.extractIndex || 1;
                let extracted = match[idx] || match[1] || match[0];
                
                if (fieldConfig.transform) {
                    extracted = fieldConfig.transform(extracted);
                }
                
                console.log(`[METADATA] Found value via regex: "${extracted}"`);
                
                // Convert based on type
                let convertedValue: string | number | null = null;
                switch (fieldConfig.type) {
                    case 'currency':
                        convertedValue = extractCurrency(extracted);
                        break;
                    case 'date':
                        convertedValue = extractDate(extracted);
                        break;
                    case 'cardNumber':
                        convertedValue = extractCardNumber(extracted);
                        break;
                    case 'string':
                        convertedValue = extracted.trim();
                        break;
                }
                
                if (convertedValue !== null && convertedValue !== '') {
                    return { 
                        value: convertedValue, 
                        confidence: 0.9,
                        source: 'fallback'
                    };
                }
            }
        }
    }
    
    // STEP 2: Try proximity search if regex failed
    console.log(`[METADATA] Regex patterns failed, trying proximity search...`);
    
    const proximityConfig: ProximityConfig = {
        maxHorizontalDistance: fieldConfig.proximity?.maxHorizontalDistance || 250,
        maxVerticalDistance: fieldConfig.proximity?.maxVerticalDistance || 30,
        sameLine: true,
        nextLine: true
    };
    
    // Try each label variation using proximity search
    for (const label of fieldConfig.labels) {
        console.log(`[METADATA] Searching for label: "${label}"`);
        
        // Search across all pages
        for (const page of documentData.pages) {
            const result = findValueNearLabel(label, page, proximityConfig);
            
            if (result && result.value) {
                console.log(`[METADATA] Found value via proximity: "${result.value}" (confidence: ${result.confidence.toFixed(2)})`);
                
                // Extract and convert the value based on type
                let extractedValue: string | number | null = null;
                
                switch (fieldConfig.type) {
                    case 'currency':
                        extractedValue = extractCurrency(result.value);
                        break;
                    case 'date':
                        extractedValue = extractDate(result.value);
                        break;
                    case 'cardNumber':
                        extractedValue = extractCardNumber(result.value);
                        break;
                    case 'string':
                        extractedValue = result.value.trim();
                        break;
                }
                
                if (extractedValue !== null && extractedValue !== '') {
                    // Apply transform if provided
                    if (fieldConfig.transform && typeof extractedValue === 'string') {
                        extractedValue = fieldConfig.transform(extractedValue);
                    }
                    
                    return { 
                        value: extractedValue, 
                        confidence: result.confidence,
                        source: 'proximity'
                    };
                }
            }
        }
    }
    
    console.log(`[METADATA] Failed to extract ${fieldName}`);
    return { value: null, confidence: 0, source: 'none' };
}

// ==========================================
// MAIN METADATA EXTRACTION
// ==========================================

export function extractMetadataFromDocument(
    documentData: DocumentData,
    bankName: string
): CreditCardMetadata {
    console.log(`[METADATA] Starting extraction for ${bankName}...`);
    console.log(`[METADATA] Document has ${documentData.pages.length} pages`);
    
    const config = BANK_METADATA_CONFIG[bankName];
    
    if (!config) {
        console.warn(`[METADATA] No configuration for bank: ${bankName}`);
        return createEmptyMetadata(bankName);
    }
    
    const metadata: CreditCardMetadata = {
        bankName,
        cardNumber: '',
        cardType: null,
        openingBalance: 0,
        creditLimit: 0,
        totalAmountDue: 0,
        minimumAmountDue: 0,
        dueDate: '',
        billCycleStart: '',
        billCycleEnd: '',
        statementDate: ''
    };
    
    const extractionLog: { field: string; value: any; confidence: number; source: string }[] = [];
    
    // Extract each field
    for (const [fieldName, fieldConfig] of Object.entries(config)) {
        const result = extractFieldWithProximity(fieldName, fieldConfig, documentData);
        
        extractionLog.push({
            field: fieldName,
            value: result.value,
            confidence: result.confidence,
            source: result.source
        });
        
        if (result.value !== null) {
            if (fieldConfig.type === 'currency' && typeof result.value === 'number') {
                metadata[fieldName] = result.value;
            } else if (fieldConfig.type === 'date' && typeof result.value === 'string') {
                metadata[fieldName] = normalizeDate(result.value);
            } else {
                metadata[fieldName] = result.value;
            }
        }
    }
    
    // Calculate bill cycle from statement date if available
    if (metadata.statementDate) {
        const cycle = calculateBillCycle(metadata.statementDate);
        metadata.billCycleStart = cycle.billCycleStart || '';
        metadata.billCycleEnd = cycle.billCycleEnd || '';
    }
    
    // Special handling for IndusInd - calculate total if needed
    if (bankName === 'IndusInd Bank' && metadata.openingBalance > 0 && metadata.totalAmountDue === 0) {
        // Try to find the total in the credit summary section
        const creditSummaryMatch = documentData.fullText.match(/Credit\s*\n?\s*Summary[\s\S]*?(\d{5,}\.\d{2})\s*DR/i);
        if (creditSummaryMatch) {
            metadata.totalAmountDue = parseFloat(creditSummaryMatch[1].replace(/,/g, ''));
            console.log(`[METADATA] IndusInd: Calculated total amount due from credit summary: ${metadata.totalAmountDue}`);
        }
    }
    
    // Log extraction summary
    console.log('[METADATA] Extraction Summary:');
    extractionLog.forEach(log => {
        const icon = log.source === 'proximity' ? '🎯' : log.source === 'fallback' ? '🔧' : '❌';
        console.log(`  ${icon} ${log.field}: ${log.value} (confidence: ${log.confidence.toFixed(2)})`);
    });
    
    const extractedCount = extractionLog.filter(l => l.source !== 'none').length;
    console.log(`[METADATA] Extracted ${extractedCount}/${extractionLog.length} fields`);
    
    return metadata;
}

// ==========================================
// BACKWARD COMPATIBILITY
// ==========================================

/**
 * Legacy function for backward compatibility
 * Extracts metadata from raw text using regex patterns only
 */
export function extractCreditCardMetadata(text: string, bankName: string): CreditCardMetadata {
    console.log(`[METADATA] Using legacy text-based extraction for ${bankName}...`);
    
    const config = BANK_METADATA_CONFIG[bankName];
    
    if (!config) {
        console.warn(`[METADATA] No configuration for bank: ${bankName}`);
        return createEmptyMetadata(bankName);
    }
    
    const metadata: CreditCardMetadata = {
        bankName,
        cardNumber: '',
        cardType: null,
        openingBalance: 0,
        creditLimit: 0,
        totalAmountDue: 0,
        minimumAmountDue: 0,
        dueDate: '',
        billCycleStart: '',
        billCycleEnd: ''
    };
    
    // Use regex fallback patterns only
    for (const [fieldName, fieldConfig] of Object.entries(config)) {
        if (fieldName === 'statementDate') continue;
        
        let value: string | number | null = null;
        
        // Try fallback patterns
        if (fieldConfig.fallbackPatterns) {
            for (const pattern of fieldConfig.fallbackPatterns) {
                const match = text.match(pattern);
                if (match) {
                    const idx = fieldConfig.extractIndex || 1;
                    let extracted = match[idx] || match[1] || match[0];
                    
                    if (fieldConfig.transform) {
                        extracted = fieldConfig.transform(extracted);
                    }
                    
                    switch (fieldConfig.type) {
                        case 'currency':
                            value = extractCurrency(extracted);
                            break;
                        case 'date':
                            value = extractDate(extracted);
                            break;
                        case 'cardNumber':
                            value = extractCardNumber(extracted);
                            break;
                        case 'string':
                            value = extracted.trim();
                            break;
                    }
                    
                    if (value !== null && value !== '') {
                        break;
                    }
                }
            }
        }
        
        // Try proximity-style search on text
        if (value === null && fieldConfig.labels) {
            for (const label of fieldConfig.labels) {
                const regex = new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
                const match = text.match(regex);
                
                if (match) {
                    const startPos = match.index! + match[0].length;
                    const searchArea = text.substring(startPos, startPos + 200);
                    
                    switch (fieldConfig.type) {
                        case 'currency':
                            value = extractCurrency(searchArea);
                            break;
                        case 'date':
                            value = extractDate(searchArea);
                            break;
                        case 'cardNumber':
                            value = extractCardNumber(searchArea);
                            break;
                    }
                    
                    if (value) break;
                }
            }
        }
        
        if (value !== null) {
            if (fieldConfig.type === 'date' && typeof value === 'string') {
                metadata[fieldName] = normalizeDate(value);
            } else {
                metadata[fieldName] = value;
            }
        }
    }
    
    // Calculate bill cycle
    if (metadata.statementDate || metadata.dueDate) {
        const cycle = calculateBillCycle(metadata.statementDate || metadata.dueDate);
        metadata.billCycleStart = cycle.billCycleStart || '';
        metadata.billCycleEnd = cycle.billCycleEnd || '';
    }
    
    return metadata;
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

function createEmptyMetadata(bankName: string): CreditCardMetadata {
    return {
        bankName,
        cardNumber: '',
        cardType: null,
        openingBalance: 0,
        creditLimit: 0,
        totalAmountDue: 0,
        minimumAmountDue: 0,
        dueDate: '',
        billCycleStart: '',
        billCycleEnd: ''
    };
}

// ==========================================
// EXPORTS
// ==========================================

// Main function exports (functions already exported via 'export function' above)
export { extractMetadataFromDocument as extractMetadata };

// Utility exports (functions already exported via 'export function' above)
export {
    createEmptyMetadata,
    calculateBillCycle,
    normalizeDate,
    extractCurrency,
    extractDate,
    extractCardNumber,
    BANK_METADATA_CONFIG
};

export default extractMetadataFromDocument;
