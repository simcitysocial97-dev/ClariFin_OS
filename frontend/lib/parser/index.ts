/**
 * Bank Statement Parser - Unified Entry Point
 * Uses semantic proximity for metadata, table detection for transactions
 * 
 * Usage:
 *   import { parseStatement } from '@/lib/parser';
 *   const result = await parseStatement(file);
 */

import { extractTextWithPositions } from './core/text-extractor';
import { detectBank } from './extractors/bank-detector';
import { extractTransactions } from './extractors/transaction-extractor';
import { extractMetadata } from './extractors/metadata-extractor';
import { validateTransactions } from './processors/validator';
import type { ParseResult } from '@/types/transaction';

// ============================================================================
// PARSING LOCK - Ensures only one PDF is parsed at a time
// ============================================================================
interface ParsingLock {
    isParsing: boolean;
    queue: Array<() => void>;
    currentFile: string | null;
}

let __PARSING_LOCK__: ParsingLock = {
    isParsing: false,
    queue: [],
    currentFile: null
};

async function acquireParsingLock(fileName: string): Promise<() => void> {
    if (__PARSING_LOCK__.isParsing) {
        console.log(`[PARSER] Waiting for lock, currently parsing: ${__PARSING_LOCK__.currentFile}`);
        await new Promise<void>(resolve => {
            __PARSING_LOCK__.queue.push(resolve);
        });
    }

    __PARSING_LOCK__.isParsing = true;
    __PARSING_LOCK__.currentFile = fileName;
    console.log(`[PARSER] Lock acquired for: ${fileName}`);

    return function releaseLock() {
        __PARSING_LOCK__.isParsing = false;
        __PARSING_LOCK__.currentFile = null;
        console.log(`[PARSER] Lock released for: ${fileName}`);
        const next = __PARSING_LOCK__.queue.shift();
        if (next) next();
    };
}

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================
export async function parseStatement(file: File): Promise<ParseResult> {
    console.log('═══════════════════════════════════════════════════════');
    console.log('🏦 SEMANTIC BANK STATEMENT PARSER v2.0');
    console.log('═══════════════════════════════════════════════════════');
    console.log('📄 File:', file.name);
    console.log('📊 Size:', (file.size / 1024).toFixed(2), 'KB');
    
    const releaseLock = await acquireParsingLock(file.name);
    
    try {
        // Step 1: Extract text WITH positions
        console.log('\n[1/5] 📝 Extracting text with spatial data...');
        const documentData = await extractTextWithPositions(file);
        
        // Step 2: Detect bank
        console.log('[2/5] 🏦 Detecting bank...');
        const bankName = detectBank(documentData.fullText);
        
        // Step 3: Extract metadata using PROXIMITY
        console.log('[3/5] 📋 Extracting metadata (proximity-based)...');
        const metadata = extractMetadata(documentData, bankName);
        console.log('      ✓ Card:', metadata.cardNumber || 'N/A');
        console.log('      ✓ Total Due: ₹', metadata.totalAmountDue);
        console.log('      ✓ Min Due: ₹', metadata.minimumAmountDue);
        
        // Step 4: Extract transactions (table detection + regex fallback)
        console.log('[4/5] 💳 Extracting transactions...');
        const transactions = extractTransactions(documentData, bankName);
        console.log('      ✓ Found', transactions.length, 'transactions');
        
        // Step 5: Validate
        console.log('[5/5] ✅ Validating totals...');
        const validation = validateTransactions(transactions, metadata);
        console.log('      ✓ Status:', validation.isValid ? 'VALID' : 'INVALID');
        console.log('      ✓ Discrepancy: ₹', validation.difference.toFixed(2));
        
        const result: ParseResult = {
            transactions,
            metadata,
            validation,
            rawText: documentData.fullText
        };
        
        console.log('\n═══════════════════════════════════════════════════════');
        console.log('✅ PARSING COMPLETE');
        console.log('═══════════════════════════════════════════════════════\n');
        
        return result;
        
    } catch (error) {
        console.error('\n❌ PARSING FAILED');
        console.error('Error:', error);
        throw new Error(`Failed to parse ${file.name}: ${(error as Error).message}`);
    } finally {
        releaseLock();
    }
}

// Re-export for advanced usage
export { extractTextWithPositions } from './core/text-extractor';
export { detectBank } from './extractors/bank-detector';
export { extractTransactions } from './extractors/transaction-extractor';
export { extractMetadata } from './extractors/metadata-extractor';
export { validateTransactions } from './processors/validator';
export { detectTransactionTable, extractTransactionsFromTable } from './semantic/table-detector';
export { findValueNearLabel } from './semantic/proximity-engine';
