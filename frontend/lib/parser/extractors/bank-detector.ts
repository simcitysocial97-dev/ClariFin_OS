/**
 * Bank Detection
 * Identifies bank from statement text
 */

const BANK_PATTERNS = [
    { regex: /HDFC\s*Bank/i, name: "HDFC Bank" },
    { regex: /ICICI\s*Bank/i, name: "ICICI Bank" },
    { regex: /SBI\s*Card|State Bank/i, name: "SBI Card" },
    { regex: /Axis\s*Bank/i, name: "Axis Bank" },
    { regex: /Kotak\s*Mahindra/i, name: "Kotak Mahindra Bank" },
    { regex: /IndusInd\s*Bank/i, name: "IndusInd Bank" },
    { regex: /Yes\s*Bank/i, name: "Yes Bank" },
    { regex: /Standard\s*Chartered/i, name: "Standard Chartered" },
    { regex: /Citibank/i, name: "Citibank" },
    { regex: /HSBC/i, name: "HSBC" },
    { regex: /American\s*Express|Amex/i, name: "American Express" },
    { regex: /RBL\s*Bank/i, name: "RBL Bank" },
    { regex: /AU\s*Small\s*Finance/i, name: "AU Small Finance Bank" },
    { regex: /IDFC\s*FIRST|IDFC\s*First/i, name: "IDFC First Bank" },
    { regex: /Federal\s*Bank/i, name: "Federal Bank" },
];

/**
 * Detect bank from document text
 */
export function detectBank(text: string): string {
    for (const pattern of BANK_PATTERNS) {
        if (pattern.regex.test(text)) {
            console.warn(`[BANK DETECTOR] Detected: ${pattern.name}`);
            return pattern.name;
        }
    }
    console.warn('[BANK DETECTOR] No bank detected, returning Unknown Bank');
    return "Unknown Bank";
}
