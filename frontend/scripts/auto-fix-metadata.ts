/**
 * Auto-Fix Metadata Extractor
 * Analyzes test failures and suggests/applies fixes
 * Run with: npx tsx scripts/auto-fix-metadata.ts
 */

import * as fs from 'fs';
import * as path from 'path';

const reportFile = path.join(__dirname, '../test-data/metadata-test-report.json');
const extractorFile = path.join(__dirname, '../lib/parser/metadata-extractor.ts');

interface FieldResult {
    expected: any;
    actual: any;
    match: boolean;
}

interface TestResult {
    file: string;
    passed: boolean;
    fields: { [key: string]: FieldResult };
    errors: string[];
}

interface Report {
    results: TestResult[];
}

function analyzeFailures(report: Report): void {
    console.log('='.repeat(60));
    console.log('ANALYZING FAILURES');
    console.log('='.repeat(60));
    
    const failures = report.results.filter(r => !r.passed);
    
    if (failures.length === 0) {
        console.log('✅ All tests passed! No fixes needed.');
        return;
    }
    
    // Group failures by field
    const fieldFailures: { [field: string]: { file: string; expected: any; actual: any }[] } = {};
    
    for (const result of failures) {
        for (const [field, data] of Object.entries(result.fields)) {
            if (!data.match) {
                if (!fieldFailures[field]) {
                    fieldFailures[field] = [];
                }
                fieldFailures[field].push({
                    file: result.file,
                    expected: data.expected,
                    actual: data.actual
                });
            }
        }
    }
    
    // Analyze each field
    for (const [field, failures] of Object.entries(fieldFailures)) {
        console.log(`\n📌 ${field} (${failures.length} failures):`);
        
        for (const failure of failures) {
            console.log(`\n   File: ${failure.file}`);
            console.log(`   Expected: ${JSON.stringify(failure.expected)}`);
            console.log(`   Actual: ${JSON.stringify(failure.actual)}`);
            
            // Generate fix suggestion based on field type
            const suggestion = generateFixSuggestion(field, failure);
            console.log(`   Suggestion: ${suggestion}`);
        }
    }
    
    // Generate combined fix code
    console.log('\n' + '='.repeat(60));
    console.log('GENERATED FIX CODE');
    console.log('='.repeat(60));
    
    generateFixCode(fieldFailures);
}

function generateFixSuggestion(field: string, failure: { file: string; expected: any; actual: any }): string {
    const bankName = getBankFromFile(failure.file);
    
    switch (field) {
        case 'cardNumber':
            if (!failure.actual || failure.actual === '') {
                return `Add card number pattern for ${bankName}`;
            }
            if (failure.actual.includes(failure.expected.slice(-4))) {
                return `Card number format issue - last 4 digits match but format differs`;
            }
            return `Wrong card number extracted - check for CKYC/KYC filter for ${bankName}`;
            
        case 'totalAmountDue':
            if (failure.actual === 0) {
                return `Total amount due not found - add pattern for ${bankName}`;
            }
            return `Wrong amount extracted - check regex pattern for ${bankName}`;
            
        case 'minimumAmountDue':
            if (failure.actual === 0) {
                return `Minimum due not found - add pattern for ${bankName}`;
            }
            return `Wrong minimum due - check pattern for ${bankName}`;
            
        case 'dueDate':
            if (!failure.actual) {
                return `Due date not found - add date pattern for ${bankName}`;
            }
            return `Date format mismatch - check date parsing for ${bankName}`;
            
        default:
            return `Check ${field} extraction logic for ${bankName}`;
    }
}

function getBankFromFile(fileName: string): string {
    const lower = fileName.toLowerCase();
    if (lower.includes('icici')) return 'ICICI Bank';
    if (lower.includes('hdfc')) return 'HDFC Bank';
    if (lower.includes('sbi')) return 'SBI Card';
    if (lower.includes('axis')) return 'Axis Bank';
    if (lower.includes('idfc')) return 'IDFC First Bank';
    if (lower.includes('indusind')) return 'IndusInd Bank';
    return 'Unknown Bank';
}

function generateFixCode(fieldFailures: { [field: string]: any[] }): void {
    console.log('\n// Add these patterns to metadata-extractor.ts:\n');
    
    for (const [field, failures] of Object.entries(fieldFailures)) {
        const banks = [...new Set(failures.map(f => getBankFromFile(f.file)))];
        
        for (const bank of banks) {
            const bankFailures = failures.filter(f => getBankFromFile(f.file) === bank);
            
            console.log(`// Fix for ${bank} - ${field}`);
            console.log(`if (bankName === '${bank}') {`);
            
            if (field === 'cardNumber') {
                console.log(`    // Expected: ${bankFailures[0].expected}`);
                console.log(`    const cardMatch = text.match(/Card\\s*(?:No\\.?|Number)[:\\s]*[Xx*]*(\\d{4})/i);`);
                console.log(`    if (cardMatch) metadata.cardNumber = \`XXXXXXXXXXXX\${cardMatch[1]}\`;`);
            } else if (field === 'totalAmountDue') {
                console.log(`    // Expected: ${bankFailures[0].expected}`);
                console.log(`    const dueMatch = text.match(/Total\\s+Amount\\s+Due[\\s:₹]*([\d,]+\\.?\\d*)/i);`);
                console.log(`    if (dueMatch) metadata.totalAmountDue = parseFloat(dueMatch[1].replace(/,/g, ''));`);
            }
            
            console.log(`}\n`);
        }
    }
}

// Main
function main(): void {
    if (!fs.existsSync(reportFile)) {
        console.error('Test report not found! Run test-metadata.ts first.');
        process.exit(1);
    }
    
    const report: Report = JSON.parse(fs.readFileSync(reportFile, 'utf-8'));
    analyzeFailures(report);
}

main();