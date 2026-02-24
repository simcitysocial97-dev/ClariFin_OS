// Run with: node scripts/generate-expected-metadata.js
const fs = require('fs');
const path = require('path');

// Import working parser from src/
const parserPath = path.join(__dirname, '../../src/parser.js');
const { parsePDFWithMetadata } = require(parserPath);

const statementsDir = path.join(__dirname, '../../test/statements');
const outputFile = path.join(__dirname, '../test-data/expected-metadata.json');

async function generateExpectedMetadata() {
    const expectedMetadata = {};
    
    const files = fs.readdirSync(statementsDir).filter(f => f.endsWith('.pdf'));
    
    for (const file of files) {
        console.log(`Processing: ${file}`);
        const pdfPath = path.join(statementsDir, file);
        const pdfData = fs.readFileSync(pdfPath);
        
        try {
            const result = await parsePDFWithMetadata(pdfData);
            expectedMetadata[file] = {
                bankName: result.metadata.bankName,
                cardNumber: result.metadata.cardNumber,
                totalAmountDue: result.metadata.totalAmountDue,
                minimumAmountDue: result.metadata.minimumAmountDue,
                creditLimit: result.metadata.creditLimit,
                dueDate: result.metadata.dueDate,
                openingBalance: result.metadata.openingBalance,
                billCycleStart: result.metadata.billCycleStart,
                billCycleEnd: result.metadata.billCycleEnd,
                transactionCount: result.transactions.length,
                validation: result.validation
            };
            console.log(`  ✓ ${file}: Card ${result.metadata.cardNumber}, Due: ₹${result.metadata.totalAmountDue}`);
        } catch (error) {
            console.error(`  ✗ ${file}: ${error.message}`);
            expectedMetadata[file] = { error: error.message };
        }
    }
    
    // Ensure output directory exists
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    fs.writeFileSync(outputFile, JSON.stringify(expectedMetadata, null, 2));
    console.log(`\nExpected metadata saved to: ${outputFile}`);
}

generateExpectedMetadata().catch(console.error);