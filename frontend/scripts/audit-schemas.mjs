// Zod Schema Audit Script
//
// This script:
// 1. Reads the OpenAPI schema from `frontend/generated/openapi-current.json`.
// 2. For each path/response, finds the corresponding Zod schema.
// 3. Reports: MATCH, MISMATCH, or MISSING.

import fs from "fs"
import path from "path"
import { fileURLToPath } from "url"

// Map DTO names to Zod schemas
const dtoToZodMap = {
  CashflowSummaryDTO: { file: "../lib/schemas/cashflow.ts", schemaName: "CashflowResponseSchema" },
  CashflowMonthlyDTO: { file: "../lib/schemas/cashflow.ts", schemaName: "CashflowMonthSchema" },
  DashboardSummaryDTO: { file: "../lib/schemas/dashboard-metrics.ts", schemaName: "DashboardMetricsSchema" },
  CreditCardSummaryDTO: { file: "../lib/schemas/cards.ts", schemaName: "CardSummarySchema" },
  TransactionDTO: { file: "../lib/schemas/transaction.ts", schemaName: "TransactionSchema" },
  ReconciliationMatchDTO: { file: "../lib/schemas/reconciliation.ts", schemaName: "ReconciliationMatchSchema" },
  NetWorthDTO: { file: "../lib/schemas/overview.ts", schemaName: "OverviewSchema" }, // No direct match
  BehaviorScoreDTO: { file: "../lib/schemas/behavior-score.ts", schemaName: "BehaviorScoreSchema" },
  AnalyticsDTO: { file: "../lib/schemas/analytics.ts", schemaName: "AnalyticsSchema" },
  WellnessScoreResponse: { file: "../lib/schemas/behavior-score.ts", schemaName: "BehaviorScoreSchema" },
}

// Helper: Check if a field is monetary (ends with _paise)
const isMonetaryField = (fieldName) => fieldName.endsWith("_paise")

// Helper: Validate Zod schema against DTO
const validateSchema = async (dtoName, dtoSchema) => {
  const zodInfo = dtoToZodMap[dtoName]
  if (!zodInfo) {
    return { status: "MISSING", mismatches: [`No Zod schema mapped for ${dtoName}`] }
  }

  // Dynamically import Zod schema
  let zodSchema
  try {
    const module = await import(zodInfo.file)
    zodSchema = module[zodInfo.schemaName]
    if (!zodSchema) {
      return { status: "MISSING", mismatches: [`Zod schema ${zodInfo.schemaName} not found in ${zodInfo.file}`] }
    }
  } catch (error) {
    return { status: "MISSING", mismatches: [`Failed to import ${zodInfo.file}: ${error}`] }
  }

  const mismatches = []
  const dtoFields = dtoSchema.properties || {}

  // Check all DTO fields exist in Zod
  for (const [fieldName] of Object.entries(dtoFields)) {
    const zodField = zodSchema.shape[fieldName]
    if (!zodField) {
      mismatches.push(`Field '${fieldName}' missing in Zod schema`)
      continue
    }

    // Check monetary fields
    if (isMonetaryField(fieldName) && !zodField._def.typeName.includes("ZodNumber")) {
      mismatches.push(`Field '${fieldName}' is not a number in Zod schema`)
    }
  }

  // Check for extra fields in Zod
  for (const fieldName of Object.keys(zodSchema.shape)) {
    if (!dtoFields[fieldName]) {
      mismatches.push(`Field '${fieldName}' in Zod schema does not exist in DTO`)
    }
  }

  return {
    status: mismatches.length === 0 ? "MATCH" : "MISMATCH",
    mismatches,
  }
}

// Main audit function
const runAudit = async () => {
  const __dirname = path.dirname(fileURLToPath(import.meta.url))
  const openApiSchema = JSON.parse(fs.readFileSync(path.join(__dirname, "../generated/openapi-current.json"), "utf-8"))

  const auditResults = {}

  for (const [_path, methods] of Object.entries(openApiSchema.paths)) {
    for (const [_method, spec] of Object.entries(methods)) {
      const responses = spec.responses || {}
      for (const [_statusCode, response] of Object.entries(responses)) {
        const content = response.content || {}
        for (const [_contentType, mediaType] of Object.entries(content)) {
          const schema = mediaType.schema || {}
          const dtoName = schema.$ref?.split("/").pop() || schema.items?.$ref?.split("/").pop()
          if (dtoName && dtoToZodMap[dtoName]) {
            const components = openApiSchema.components?.schemas || {}
            const dtoSchema = components[dtoName]
            if (dtoSchema) {
              auditResults[dtoName] = await validateSchema(dtoName, dtoSchema)
            }
          }
        }
      }
    }
  }

  // Report results
  console.log("=== ZOD SCHEMA AUDIT REPORT ===\n")

  let totalMismatches = 0
  let totalMissing = 0

  for (const [dtoName, result] of Object.entries(auditResults)) {
    console.log(`DTO: ${dtoName}`)
    console.log(`Status: ${result.status}`)
    if (result.mismatches.length > 0) {
      console.log("Mismatches:")
      for (const mismatch of result.mismatches) {
        console.log(`  - ${mismatch}`)
      }
      if (result.status === "MISMATCH") totalMismatches++
      if (result.status === "MISSING") totalMissing++
    }
    console.log()
  }

  console.log("=== SUMMARY ===")
  console.log(`Total DTOs audited: ${Object.keys(auditResults).length}`)
  console.log(`Mismatches: ${totalMismatches}`)
  console.log(`Missing: ${totalMissing}`)

  if (totalMismatches === 0 && totalMissing === 0) {
    console.log("✅ All schemas match their DTOs!")
  } else {
    console.log("❌ Schema mismatches detected. See report above.")
    process.exit(1)
  }
}

runAudit()
