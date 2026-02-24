# Bank Statement Parser - Architecture

## 📁 File Structure (Clean Architecture)

### src/ - Node.js CLI/Testing Only
**NEVER import these files in the Next.js app**

- `parser.js` - Reference implementation for CLI
- `categorizer.js` - Reference categorizer
- `metadata-proximity.js` - Reference metadata extractor

These files are kept for:
- Command-line usage
- Test validation
- Reference implementation

### nextjs-app/lib/parser/ - Single Source of Truth
**The app ONLY uses these files**

```
lib/parser/
├── index.ts              ⭐ MAIN ENTRY POINT - Import this only
├── categorizer.ts        🏷️ Transaction categorization (legacy, unused)
└── metadata-extractor.ts 📋 Metadata extraction (legacy, unused)
```

**Note:** The `index.ts` file now contains ALL parsing logic in one unified module:
- PDF text extraction
- Bank detection
- Transaction parsing
- Metadata extraction
- Validation

This eliminates the confusion of multiple files and ensures the app uses a single, consistent parser.

## 🎯 Usage

### Correct Way ✅
```typescript
import { parseStatement } from '@/lib/parser';

const result = await parseStatement(file);
// result.transactions
// result.metadata
// result.validation
```

### Wrong Ways ❌
```typescript
// DON'T DO THIS:
import { parsePDF } from '../../src/parser';           // ❌ Wrong path
import { parseStatement } from '../parser/old-file'; // ❌ Old file
import parser from '/public/parser/browser-parser';  // ❌ Public folder
import { parsePDFWithMetadata } from './browser-parser'; // ❌ Deleted file
```

## 🔒 Import Rules

1. ✅ App imports ONLY from `'@/lib/parser'`
2. ✅ Use single entry point: `import { parseStatement } from '@/lib/parser'`
3. ❌ Never import from `src/`
4. ❌ Never import from `public/`
5. ❌ Never use old `browser-parser.js/ts`

## 🧪 Testing

```bash
# Build (includes TypeScript checking)
npm run build

# Run tests
npm test
```

## 📊 Data Flow

```
User uploads PDF
      ↓
UploadModal (React Component)
      ↓
parseStatement (lib/parser/index.ts)
      ↓
├─→ extractTextFromPDF (PDF.js)
├─→ detectBank (regex patterns)
├─→ parseTransactions (regex patterns)
├─→ extractMetadata (bank-specific patterns)
└─→ validateTransactions (math validation)
      ↓
Return ParseResult
      ↓
Zustand Store (addCard, addTransactions)
      ↓
React Components (Cards, Transactions, Dashboard)
```

## 🔍 Debugging

Check browser console for the new unified parser logs:

```
═══════════════════════════════════════════════════════
🏦 BANK STATEMENT PARSER v2.0
═══════════════════════════════════════════════════════
📄 File: statement.pdf
📊 Size: 245.67 KB

[1/5] 📝 Extracting text from PDF...
      ✓ Extracted 15432 characters

[2/5] 🏦 Detecting bank...
      ✓ Detected: HDFC Bank

[3/5] 💳 Parsing transactions...
      ✓ Found 12 transactions

[4/5] 📋 Extracting metadata...
      ✓ Card: XXXX XXXX XXXX XX1234
      ✓ Total Due: ₹ 45000.00
      ✓ Min Due: ₹ 2250.00

[5/5] ✅ Validating totals...
      ✓ Status: VALID
      ✓ Discrepancy: ₹ 0.00

═══════════════════════════════════════════════════════
✅ PARSING COMPLETE
═══════════════════════════════════════════════════════
```

If you don't see these logs, check that:
1. You're importing from `@/lib/parser`
2. The `index.ts` file exists in `lib/parser/`
3. No old imports are being used

## 🗑️ Deleted Files (No Longer Needed)

The following files have been removed to eliminate confusion:

- `public/parser/browser-parser.js` - ❌ Deleted
- `lib/parser/browser-parser.ts` - ❌ Deleted
- `app/parser/browser-parser.js` - ❌ Deleted (if existed)

## 📝 Migration Guide

If you have old code using the previous parser:

### Before:
```typescript
// OLD - Don't use this
import { parsePDFWithMetadata } from '@/lib/parser/browser-parser';
const result = await parsePDFWithMetadata(arrayBuffer);
```

### After:
```typescript
// NEW - Use this
import { parseStatement } from '@/lib/parser';
const result = await parseStatement(file);
```

## 🎉 Benefits of New Architecture

1. **Single Source of Truth**: One file contains all parsing logic
2. **No Confusion**: Clear import path `@/lib/parser`
3. **Type Safety**: Full TypeScript support
4. **Better Debugging**: Comprehensive console logging
5. **Easier Maintenance**: All logic in one place
6. **No Duplicates**: Eliminated multiple parser files

## 🔧 Troubleshooting

### "Cannot find module '@/lib/parser'"
- Check that `lib/parser/index.ts` exists
- Verify tsconfig.json has correct path aliases

### "parseStatement is not a function"
- Ensure you're importing correctly: `import { parseStatement } from '@/lib/parser'`
- Don't use default import

### Old parser still being used
- Search for `BankParser` in your codebase
- Remove any `window.BankParser` references
- Delete old browser-parser.js files

### Metadata not extracting correctly
- Check console logs for bank detection
- Verify bank-specific patterns in index.ts
- Ensure PDF text is being extracted
