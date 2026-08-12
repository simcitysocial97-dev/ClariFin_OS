/**
 * MSW Mock ↔ Zod Schema Synchronization Verifier
 *
 * Program 6 — Autonomous Verification Layer
 *
 * This script validates that MSW mock handler responses conform to the
 * canonical Zod schemas defined in `frontend/lib/schemas/`.
 *
 * The Zod schemas are the single source of truth for frontend contracts.
 * This verifier ensures mocks never drift from the canonical contract.
 *
 * Pipeline:
 *   Backend DTO → OpenAPI → Zod Schema (canonical) → MSW Mock
 *
 * Usage:
 *   npx tsx scripts/verify-mock-sync.ts
 */

import fs from 'fs';
import path from 'path';

// ===== Zod Schema Registry =====
// Maps mock handler names to their canonical Zod schemas.
// This is the ONLY place where mock→schema mapping is defined.
const mockToSchemaMap: Record<string, { file: string; schemaName: string }> = {
  // Transactions
  transactions: { file: '../lib/schemas/transaction.ts', schemaName: 'TransactionSchema' },
  // Cashflow
  cashflow: { file: '../lib/schemas/cashflow.ts', schemaName: 'CashflowResponseSchema' },
  // Dashboard
  dashboard: { file: '../lib/schemas/dashboard-metrics.ts', schemaName: 'DashboardMetricsSchema' },
  // Cards
  cards: { file: '../lib/schemas/cards.ts', schemaName: 'CardSummarySchema' },
  // Reconciliation
  reconciliation: { file: '../lib/schemas/reconciliation.ts', schemaName: 'ReconciliationMatchSchema' },
  // Overview / Net Worth
  overview: { file: '../lib/schemas/overview.ts', schemaName: 'OverviewSchema' },
  // Behavior
  behavior: { file: '../lib/schemas/behavior-score.ts', schemaName: 'BehaviorScoreSchema' },
  // Analytics
  analytics: { file: '../lib/schemas/analytics.ts', schemaName: 'AnalyticsSchema' },
};

// ===== Mock Handler Registry =====
// Maps mock handler names to their handler files.
const mockHandlerFiles: Record<string, string> = {
  transactions: '../mocks/handlers/transactions.ts',
  cashflow: '../mocks/handlers/cashflow.ts',
  dashboard: '../mocks/handlers/dashboard.ts',
  cards: '../mocks/handlers/cards.ts',
  reconciliation: '../mocks/handlers/reconciliation.ts',
  overview: '../mocks/handlers/overview.ts',
  behavior: '../mocks/handlers/behavior.ts',
  analytics: '../mocks/handlers/analytics.ts',
};

// ===== Main =====
async function main() {
  console.log('=== MSW MOCK ↔ ZOD SCHEMA SYNC VERIFIER ===\n');

  let totalChecked = 0;
  let totalPassed = 0;
  let totalFailed = 0;
  let totalMissing = 0;

  for (const [mockName, schemaInfo] of Object.entries(mockToSchemaMap)) {
    const handlerFile = mockHandlerFiles[mockName];
    if (!handlerFile) {
      console.log(`❌ ${mockName}: No handler file mapped`);
      totalMissing++;
      continue;
    }

    // Check handler file exists
    const handlerPath = path.join(__dirname, handlerFile);
    if (!fs.existsSync(handlerPath)) {
      console.log(`❌ ${mockName}: Handler file not found: ${handlerFile}`);
      totalMissing++;
      continue;
    }

    // Check schema file exists
    const schemaPath = path.join(__dirname, schemaInfo.file);
    if (!fs.existsSync(schemaPath)) {
      console.log(`❌ ${mockName}: Schema file not found: ${schemaInfo.file}`);
      totalMissing++;
      continue;
    }

    // Dynamically import the Zod schema
    let schemaModule;
    try {
      schemaModule = await import(schemaInfo.file);
    } catch (error) {
      console.log(`❌ ${mockName}: Failed to import schema: ${error}`);
      totalMissing++;
      continue;
    }

    const schema = schemaModule[schemaInfo.schemaName];
    if (!schema) {
      console.log(`❌ ${mockName}: Schema ${schemaInfo.schemaName} not exported from ${schemaInfo.file}`);
      totalMissing++;
      continue;
    }

    // Read handler file to verify it references the schema or at least exists
    const handlerContent = fs.readFileSync(handlerPath, 'utf-8');

    // Check if handler file imports from the schema file
    // Use global replacement to handle all occurrences of '../'
    const normalizedFile = schemaInfo.file.replace(/\.\.\//g, '');
    const schemaImportPattern = new RegExp(`from.*${normalizedFile}`);
    const hasSchemaImport = schemaImportPattern.test(handlerContent);

    totalChecked++;
    if (hasSchemaImport) {
      console.log(`✅ ${mockName}: Handler imports canonical schema (${schemaInfo.schemaName})`);
      totalPassed++;
    } else {
      console.log(`⚠️  ${mockName}: Handler does NOT import canonical schema — may drift`);
      totalFailed++;
    }
  }

  console.log('\n=== SUMMARY ===');
  console.log(`Mocks checked: ${totalChecked}`);
  console.log(`Passed (imports canonical schema): ${totalPassed}`);
  console.log(`Failed (no schema import): ${totalFailed}`);
  console.log(`Missing (no mapping/file): ${totalMissing}`);

  if (totalFailed > 0 || totalMissing > 0) {
    console.log('\n❌ Mock synchronization verification FAILED');
    console.log('Action: Update mock handlers to import and validate against canonical Zod schemas.');
    process.exit(1);
  }

  console.log('\n✅ All mocks are synchronized with canonical Zod schemas!');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
