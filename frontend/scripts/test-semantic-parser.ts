/**
 * Comprehensive test for the new semantic-proximity parser
 * Tests all 7 bank PDFs and compares with expected results
 */

import * as fs from 'fs';
import * as path from 'path';

// Dynamic import for ES module compatibility
async function runTests() {
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('  SEMANTIC PARSER VALIDATION TEST');
    console.log('═══════════════════════════════════════════════════════════════\n');

    const testDir = path.join(__dirname, '../../test/statements');
    const expectedDir = path.join(__dirname, '../../test/expected');

    // Get all PDF files
    const pdfFiles = fs.readdirSync(testDir).filter(f => f.endsWith('.pdf'));

    console.log(`Found ${pdfFiles.length} PDF files to test\n`);

    const results: Array<{
        file: string;
        bank: string;
        transactionCount: { expected: number; actual: number; match: boolean };
        metadata: { cardNumber: boolean; totalDue: boolean; minDue: boolean };
        validation: { isValid: boolean; difference: number };
        status: 'PASS' | 'FAIL' | 'PARTIAL';
    }> = [];

    for (const pdfFile of pdfFiles) {
        console.log(`\n📄 Testing: ${pdfFile}`);
        console.log('─'.repeat(50));

        try {
            // Read PDF as buffer
            const pdfPath = path.join(testDir, pdfFile);
            const pdfBuffer = fs.readFileSync(pdfPath);

            // Create File-like object for Node.js
            const file = {
                name: pdfFile,
                arrayBuffer: async () => pdfBuffer.buffer.slice(
                    pdfBuffer.byteOffset,
                    pdfBuffer.byteOffset + pdfBuffer.byteLength
                )
            };

            // Import parser dynamically
            const { parseStatement } = await import('../lib/parser');

            // Parse the PDF
            const result = await parseStatement(file as unknown as File);

            // Load expected results
            const expectedFile = pdfFile.replace('.pdf', '.json');
            const expectedPath = path.join(expectedDir, expectedFile);

            let expectedTransactions: any[] = [];
            if (fs.existsSync(expectedPath)) {
                const expectedData = JSON.parse(fs.readFileSync(expectedPath, 'utf-8'));
                // Expected JSON is either an array of transactions or an object with transactions property
                expectedTransactions = Array.isArray(expectedData) ? expectedData : (expectedData.transactions || []);
            }

            // Compare results
            const testResult = {
                file: pdfFile,
                bank: result.metadata.bankName,
                transactionCount: {
                    expected: expectedTransactions.length,
                    actual: result.transactions.length,
                    match: result.transactions.length === expectedTransactions.length
                },
                metadata: {
                    cardNumber: !!result.metadata.cardNumber && result.metadata.cardNumber.length > 4,
                    totalDue: result.metadata.totalAmountDue > 0,
                    minDue: result.metadata.minimumAmountDue >= 0
                },
                validation: {
                    isValid: result.validation.isValid,
                    difference: result.validation.difference || 0
                },
                status: 'PASS' as 'PASS' | 'FAIL' | 'PARTIAL'
            };

            // Determine status
            const metadataOk = testResult.metadata.cardNumber && testResult.metadata.totalDue;
            const txnOk = testResult.transactionCount.match;

            if (metadataOk && txnOk && testResult.validation.isValid) {
                testResult.status = 'PASS';
            } else if (metadataOk || txnOk) {
                testResult.status = 'PARTIAL';
            } else {
                testResult.status = 'FAIL';
            }

            results.push(testResult);

            // Print result
            console.log(`   Bank: ${result.metadata.bankName}`);
            console.log(`   Card: ${result.metadata.cardNumber || 'NOT FOUND'}`);
            console.log(`   Total Due: ₹${result.metadata.totalAmountDue || 0}`);
            console.log(`   Min Due: ₹${result.metadata.minimumAmountDue || 0}`);
            console.log(`   Transactions: ${result.transactions.length} (expected: ${expectedTransactions.length || 'N/A'})`);
            console.log(`   Validation: ${result.validation.isValid ? '✓ VALID' : '✗ INVALID'}`);
            console.log(`   Status: ${testResult.status === 'PASS' ? '✅ PASS' : testResult.status === 'PARTIAL' ? '⚠️ PARTIAL' : '❌ FAIL'}`);

        } catch (error) {
            console.error(`   ❌ ERROR: ${(error as Error).message}`);
            results.push({
                file: pdfFile,
                bank: 'ERROR',
                transactionCount: { expected: 0, actual: 0, match: false },
                metadata: { cardNumber: false, totalDue: false, minDue: false },
                validation: { isValid: false, difference: 0 },
                status: 'FAIL'
            });
        }
    }

    // Summary
    console.log('\n');
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('  TEST SUMMARY');
    console.log('═══════════════════════════════════════════════════════════════\n');

    const passed = results.filter(r => r.status === 'PASS').length;
    const partial = results.filter(r => r.status === 'PARTIAL').length;
    const failed = results.filter(r => r.status === 'FAIL').length;

    console.log(`   ✅ Passed:  ${passed}/${results.length}`);
    console.log(`   ⚠️  Partial: ${partial}/${results.length}`);
    console.log(`   ❌ Failed:  ${failed}/${results.length}`);
    console.log(`\n   Success Rate: ${((passed / results.length) * 100).toFixed(1)}%`);

    // Detailed failure report
    if (failed > 0 || partial > 0) {
        console.log('\n   Issues Found:');
        results.filter(r => r.status !== 'PASS').forEach(r => {
            console.log(`\n   📌 ${r.file}:`);
            if (!r.metadata.cardNumber) console.log('      - Card number not extracted');
            if (!r.metadata.totalDue) console.log('      - Total due not extracted');
            if (!r.transactionCount.match) {
                console.log(`      - Transaction count mismatch: got ${r.transactionCount.actual}, expected ${r.transactionCount.expected}`);
            }
            if (!r.validation.isValid) {
                console.log(`      - Validation failed, difference: ₹${r.validation.difference.toFixed(2)}`);
            }
        });
    }

    // Save report
    const report = {
        timestamp: new Date().toISOString(),
        summary: { total: results.length, passed, partial, failed },
        results
    };

    const reportPath = path.join(__dirname, '../test-data/semantic-parser-report.json');
    fs.mkdirSync(path.dirname(reportPath), { recursive: true });
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log(`\n   Report saved: ${reportPath}`);

    return failed === 0;
}

runTests()
    .then(success => process.exit(success ? 0 : 1))
    .catch(err => {
        console.error('Test runner failed:', err);
        process.exit(1);
    });
