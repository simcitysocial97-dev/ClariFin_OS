/**
 * Metadata Extractor Test Suite
 * Run with: npx tsx scripts/test-metadata.ts
 */

import * as fs from 'fs';
import * as path from 'path';

// Use legacy build for Node.js
const pdfjsLib = require('pdfjs-dist/legacy/build/pdf.js');
pdfjsLib.GlobalWorkerOptions.workerSrc = require.resolve(
    'pdfjs-dist/legacy/build/pdf.worker.js'
);

// Import the metadata extractor we're testing
import { extractCreditCardMetadata, Metadata } from '../lib/parser/metadata-extractor';

// Types
interface ExpectedMetadata {
    bankName: string;
    cardNumber: string;
    totalAmountDue: number;
    minimumAmountDue: number;
    creditLimit: number;
    dueDate: string;
    openingBalance: number;
    billCycleStart: string;
    billCycleEnd: string;
    transactionCount: number;
}

interface TestResult {
    file: string;
    passed: boolean;
    fields: {
        [key: string]: {
            expected: any;
            actual: any;
            match: boolean;
        };
    };
    errors: string[];
}

// Paths
const statementsDir = path.join(__dirname, '../../test/statements');
const expectedMetadataFile = path.join(__dirname, '../test-data/expected-metadata.json');
const reportFile = path.join(__dirname, '../test-data/metadata-test-report.json');

// Bank detection patterns (copy from browser-parser.ts)
const BANK_PATTERNS = [
    { regex: /HDFC\s*Bank/i, name: "HDFC Bank" },
    { regex: /ICICI\s*Bank/i, name: "ICICI Bank" },
    { regex: /SBI\s*Card|State Bank/i, name: "SBI Card" },
    { regex: /Axis\s*Bank/i, name: "Axis Bank" },
    { regex: /IndusInd\s*Bank/i, name: "IndusInd Bank" },
    { regex: /IDFC\s*FIRST|IDFC\s*First/i, name: "IDFC First Bank" },
];

function detectBank(text: string): string {
    for (const pattern of BANK_PATTERNS) {
        if (pattern.regex.test(text)) {
            return pattern.name;
        }
    }
    return "Unknown Bank";
}

async function extractTextFromPDF(pdfPath: string): Promise<string> {
    const buffer = fs.readFileSync(pdfPath);
    // Convert Buffer to Uint8Array
    const data = new Uint8Array(buffer.buffer, buffer.byteOffset, buffer.byteLength);
    const pdf = await pdfjsLib.getDocument({ data }).promise;
    
    let fullText = '';
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        
        let lastY: number | null = null;
        let pageText = '';
        
        for (const item of textContent.items) {
            const textItem = item as any;
            if (lastY !== null && Math.abs(textItem.transform[5] - lastY) > 5) {
                pageText += '\n';
            }
            pageText += textItem.str + ' ';
            lastY = textItem.transform[5];
        }
        
        fullText += pageText + '\n';
    }
    
    return fullText;
}

function compareValues(expected: any, actual: any, fieldName: string): boolean {
    // Handle numbers with tolerance
    if (typeof expected === 'number' && typeof actual === 'number') {
        return Math.abs(expected - actual) < 1; // ₹1 tolerance
    }
    
    // Handle card numbers - compare last 4 digits
    if (fieldName === 'cardNumber') {
        const expectedLast4 = String(expected).slice(-4);
        const actualLast4 = String(actual).slice(-4);
        return expectedLast4 === actualLast4;
    }
    
    // Handle dates - normalize and compare
    if (fieldName.includes('date') || fieldName.includes('Date')) {
        // Basic comparison - could be enhanced
        return String(expected).replace(/[\s\-\/]/g, '') === String(actual).replace(/[\s\-\/]/g, '');
    }
    
    // String comparison
    return String(expected).toLowerCase() === String(actual).toLowerCase();
}

async function testSinglePDF(
    pdfPath: string, 
    expected: ExpectedMetadata
): Promise<TestResult> {
    const fileName = path.basename(pdfPath);
    const result: TestResult = {
        file: fileName,
        passed: true,
        fields: {},
        errors: []
    };
    
    try {
        // Extract text
        const text = await extractTextFromPDF(pdfPath);
        
        // Detect bank
        const bankName = detectBank(text);
        
        // Run metadata extractor
        const metadata = extractCreditCardMetadata(text, bankName);
        
        // Compare each field
        const fieldsToCheck = [
            'bankName',
            'cardNumber',
            'totalAmountDue',
            'minimumAmountDue',
            'creditLimit',
            'dueDate',
            'openingBalance'
        ];
        
        for (const field of fieldsToCheck) {
            const expectedValue = (expected as any)[field];
            const actualValue = (metadata as any)[field];
            const match = compareValues(expectedValue, actualValue, field);
            
            result.fields[field] = {
                expected: expectedValue,
                actual: actualValue,
                match
            };
            
            if (!match) {
                result.passed = false;
                result.errors.push(`${field}: expected "${expectedValue}", got "${actualValue}"`);
            }
        }
        
    } catch (error) {
        result.passed = false;
        result.errors.push(`Error: ${(error as Error).message}`);
    }
    
    return result;
}

async function runAllTests(): Promise<void> {
    console.log('='.repeat(60));
    console.log('METADATA EXTRACTOR TEST SUITE');
    console.log('='.repeat(60));
    
    // Load expected metadata
    if (!fs.existsSync(expectedMetadataFile)) {
        console.error('Expected metadata file not found!');
        console.error('Run: node scripts/generate-expected-metadata.js first');
        process.exit(1);
    }
    
    const expectedData = JSON.parse(fs.readFileSync(expectedMetadataFile, 'utf-8'));
    
    // Get all PDF files
    const pdfFiles = fs.readdirSync(statementsDir).filter(f => f.endsWith('.pdf'));
    
    const allResults: TestResult[] = [];
    let passed = 0;
    let failed = 0;
    
    for (const file of pdfFiles) {
        const pdfPath = path.join(statementsDir, file);
        const expected = expectedData[file];
        
        if (!expected || expected.error) {
            console.log(`\n⚠️  ${file}: No expected data (skipped)`);
            continue;
        }
        
        console.log(`\n📄 Testing: ${file}`);
        const result = await testSinglePDF(pdfPath, expected);
        allResults.push(result);
        
        if (result.passed) {
            passed++;
            console.log(`   ✅ PASSED`);
        } else {
            failed++;
            console.log(`   ❌ FAILED`);
            for (const error of result.errors) {
                console.log(`      - ${error}`);
            }
        }
        
        // Show field comparison
        console.log('   Fields:');
        for (const [field, data] of Object.entries(result.fields)) {
            const icon = data.match ? '✓' : '✗';
            console.log(`      ${icon} ${field}: ${data.actual} (expected: ${data.expected})`);
        }
    }
    
    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('SUMMARY');
    console.log('='.repeat(60));
    console.log(`Total: ${passed + failed}`);
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);
    
    // Save detailed report
    const report = {
        timestamp: new Date().toISOString(),
        summary: { total: passed + failed, passed, failed },
        results: allResults
    };
    
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    console.log(`\nDetailed report saved to: ${reportFile}`);
    
    // Generate fix suggestions
    if (failed > 0) {
        console.log('\n' + '='.repeat(60));
        console.log('FIX SUGGESTIONS');
        console.log('='.repeat(60));
        
        for (const result of allResults.filter(r => !r.passed)) {
            console.log(`\n📌 ${result.file}:`);
            for (const [field, data] of Object.entries(result.fields)) {
                if (!data.match) {
                    console.log(`   ${field}:`);
                    console.log(`     Expected: ${JSON.stringify(data.expected)}`);
                    console.log(`     Got: ${JSON.stringify(data.actual)}`);
                    console.log(`     Suggestion: Check ${field} extraction pattern for this bank`);
                }
            }
        }
    }
}

// Run tests
runAllTests().catch(console.error);