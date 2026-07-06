/**
 * Step-by-step parser debugging
 * Run for a single PDF to see exactly what happens at each stage
 */

import * as fs from 'fs';
import * as path from 'path';

async function debugParse(pdfFile: string) {
    const testDir = path.join(__dirname, '../../test/statements');
    const pdfPath = path.join(testDir, pdfFile);

    if (!fs.existsSync(pdfPath)) {
        console.error(`File not found: ${pdfPath}`);
        process.exit(1);
    }

    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`  DEBUGGING: ${pdfFile}`);
    console.log('═══════════════════════════════════════════════════════════════\n');

    const pdfBuffer = fs.readFileSync(pdfPath);
    const file = {
        name: pdfFile,
        arrayBuffer: async () => pdfBuffer.buffer.slice(
            pdfBuffer.byteOffset,
            pdfBuffer.byteOffset + pdfBuffer.byteLength
        )
    };

    // Step 1: Text Extraction
    console.log('STEP 1: TEXT EXTRACTION');
    console.log('─'.repeat(60));

    const { extractTextWithPositions } = await import('../lib/parser/core/text-extractor');
    const documentData = await extractTextWithPositions(file as unknown as File);

    console.log(`Pages: ${documentData.pages.length}`);
    console.log(`Total text length: ${documentData.fullText.length} chars`);
    console.log(`First 500 chars:\n${documentData.fullText.substring(0, 500)}...`);

    // Step 2: Bank Detection
    console.log('\n\nSTEP 2: BANK DETECTION');
    console.log('─'.repeat(60));

    const { detectBank } = await import('../lib/parser/extractors/bank-detector');
    const bankName = detectBank(documentData.fullText);
    console.log(`Detected bank: ${bankName}`);

    // Step 3: Metadata Extraction
    console.log('\n\nSTEP 3: METADATA EXTRACTION (Proximity-based)');
    console.log('─'.repeat(60));

    const { extractMetadata } = await import('../lib/parser/extractors/metadata-extractor');
    const metadata = extractMetadata(documentData, bankName);
    console.log('Extracted metadata:');
    console.log(JSON.stringify(metadata, null, 2));

    // Step 4: Table Detection
    console.log('\n\nSTEP 4: TABLE DETECTION');
    console.log('─'.repeat(60));

    const { detectTransactionTable } = await import('../lib/parser/semantic/table-detector');

    for (let i = 0; i < documentData.pages.length; i++) {
        console.log(`\nPage ${i + 1}:`);
        const table = detectTransactionTable(documentData.pages[i]);
        if (table) {
            console.log(`  ✓ Table found!`);
            console.log(`  Headers: ${table.headers.map(h => h.name).join(', ')}`);
            console.log(`  Rows: ${table.rows.length}`);
            console.log(`  First row: ${table.rows[0]?.cells.join(' | ')}`);
        } else {
            console.log(`  ✗ No table detected`);
        }
    }

    // Step 5: Transaction Extraction
    console.log('\n\nSTEP 5: TRANSACTION EXTRACTION');
    console.log('─'.repeat(60));

    const { extractTransactions } = await import('../lib/parser/extractors/transaction-extractor');
    const transactions = extractTransactions(documentData, bankName);

    console.log(`Found ${transactions.length} transactions`);
    console.log('\nFirst 5 transactions:');
    transactions.slice(0, 5).forEach((t, i) => {
        console.log(`  ${i + 1}. ${t.date} | ${t.description.substring(0, 30)}... | ₹${(t.amount_paise / 100).toFixed(2)} | ${t.type}`);
    });

    // Step 6: Validation
    console.log('\n\nSTEP 6: VALIDATION');
    console.log('─'.repeat(60));

    const { validateTransactions } = await import('../lib/parser/processors/validator');
    const validation = validateTransactions(transactions, metadata);

    console.log(`Total debits: ₹${validation.totalDebits}`);
    console.log(`Total credits: ₹${validation.totalCredits}`);
    console.log(`Calculated total: ₹${validation.calculatedTotal}`);
    console.log(`Bank stated total: ₹${validation.bankTotal}`);
    console.log(`Difference: ₹${validation.difference}`);
    console.log(`Valid: ${validation.isValid ? 'YES' : 'NO'}`);

    console.log('\n═══════════════════════════════════════════════════════════════');
    console.log('  DEBUG COMPLETE');
    console.log('═══════════════════════════════════════════════════════════════\n');
}

// Get PDF file from command line argument
const pdfFile = process.argv[2] || 'icici_feb.pdf';
debugParse(pdfFile).catch(console.error);