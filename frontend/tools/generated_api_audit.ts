/**
 * Phase 4 — Generated API Audit
 *
 * Validates the backend contract integration chain:
 * - Generated types exist and are up to date
 * - Hooks only import generated types
 * - Components never import generated types directly
 * - API client contract matches expected shape
 */

import * as ts from 'typescript'
import * as path from 'path'
import type { AuditIssue, AuditResult } from './types'
import { walkTsFiles, resolveFrontend, createResult, readTextFile, readJsonFile } from './utils'

export async function runGeneratedApiAudit(): Promise<AuditResult> {
  const start = Date.now()
  const issues: AuditIssue[] = []

  const hooksDir = resolveFrontend('lib', 'hooks')
  const apiSchemaPath = resolveFrontend('api-schema.json')

  // Check 1: Generated types exist
  const generatedApiTypes = resolveFrontend('types', 'api-generated.ts')
  const generatedTypesContent = readTextFile(generatedApiTypes)
  if (!generatedTypesContent) {
    issues.push({
      severity: 'error',
      code: 'MISSING_GENERATED_TYPES',
      message: 'Generated API types not found at types/api-generated.ts',
      suggestion: 'Run `npm run gen:types` to generate types from the backend OpenAPI schema.',
    })
  } else {
    // Check that generated types are not empty
    if (generatedTypesContent.trim().length < 100) {
      issues.push({
        severity: 'warning',
        code: 'EMPTY_GENERATED_TYPES',
        message: 'types/api-generated.ts appears to be empty or contains only boilerplate.',
        suggestion: 'Regenerate with `npm run gen:types` while the backend is running.',
      })
    }

    // Check that generated types reference backend operations
    if (!generatedTypesContent.includes('paths') && !generatedTypesContent.includes('operations')) {
      issues.push({
        severity: 'warning',
        code: 'INCOMPLETE_GENERATED_TYPES',
        message: 'Generated types may not contain backend API paths or operations.',
        suggestion: 'Verify that the backend OpenAPI schema is accessible at http://localhost:8000/openapi.json',
      })
    }
  }

  // Check 2: API schema file exists
  const apiSchema = readJsonFile(apiSchemaPath)
  if (!apiSchema) {
    issues.push({
      severity: 'warning',
      code: 'MISSING_API_SCHEMA',
      message: 'API schema snapshot not found at api-schema.json',
      suggestion: 'Run the backend server and capture the schema snapshot.',
    })
  }

  // Check 3: API client exists and uses generated types
  const apiClientContent = readTextFile(resolveFrontend('lib', 'api', 'client.ts'))
  if (!apiClientContent) {
    issues.push({
      severity: 'error',
      code: 'MISSING_API_CLIENT',
      message: 'API client not found at lib/api/client.ts',
      suggestion: 'Create an API client that uses the generated types.',
    })
  } else {
    // Check client imports generated types
    if (!apiClientContent.includes('api-generated') && !apiClientContent.includes('api-schema')) {
      issues.push({
        severity: 'warning',
        code: 'CLIENT_NOT_USING_GENERATED_TYPES',
        message: 'API client does not import generated types. It may be using raw fetch responses.',
        suggestion: 'Import types from types/api-generated.ts for type-safe API calls.',
      })
    }
  }

  // Check 4: Hooks only import from generated types, not from types/ directly (if types exists)
  if (generatedTypesContent) {
    const hookFiles = walkTsFiles(hooksDir)
    for (const filePath of hookFiles) {
      const content = readTextFile(filePath)
      if (!content) continue
      const relativePath = path.relative(resolveFrontend(), filePath)

      // Parse imports
      const sourceFile = ts.createSourceFile(
        path.basename(filePath),
        content,
        ts.ScriptTarget.Latest,
        true,
      )

      const imports: Array<{ moduleName: string; namedImports: string[] }> = []
      ts.forEachChild(sourceFile, (node) => {
        if (ts.isImportDeclaration(node) && node.moduleSpecifier) {
          const moduleName = node.moduleSpecifier.getText(sourceFile).replace(/['"]/g, '')
          const namedImports: string[] = []
          if (node.importClause?.namedBindings && ts.isNamedImports(node.importClause.namedBindings)) {
            for (const element of node.importClause.namedBindings.elements) {
              namedImports.push(element.name.getText(sourceFile))
            }
          }
          imports.push({ moduleName, namedImports })
        }
      })

      // Check if hooks import from non-generated type files
      for (const imp of imports) {
        if (imp.moduleName.includes('../types/') && !imp.moduleName.includes('api-generated')) {
          issues.push({
            severity: 'warning',
            code: 'HOOK_IMPORTS_NON_GENERATED_TYPE',
            file: relativePath,
            message: `Hook imports from "${imp.moduleName}" instead of generated types.`,
            suggestion: 'Consider moving type definitions to types/api-generated.ts or creating a ViewModel in the hook.',
          })
        }
      }

      // Check hooks don't export 'any'
      if (content.includes(': any')) {
        issues.push({
          severity: 'warning',
          code: 'HOOK_USES_ANY',
          file: relativePath,
          message: 'Hook uses `any` type. This bypasses the generated API types.',
          suggestion: 'Replace `any` with the proper generated type from types/api-generated.ts',
        })
      }
    }
  }

  // Check 5: Components don't import generated types directly
  const componentFiles = walkTsFiles(resolveFrontend('components'))
  for (const filePath of componentFiles) {
    const content = readTextFile(filePath)
    if (!content) continue
    const relativePath = path.relative(resolveFrontend(), filePath)

    const importRegex = /from\s+['"](?:\.\.\/)*types\/(?:api-generated)/g
    if (importRegex.test(content)) {
      issues.push({
        severity: 'error',
        code: 'COMPONENT_IMPORTS_GENERATED_TYPES',
        file: relativePath,
        message: 'Component directly imports from generated API types. Components should only use ViewModels from hooks.',
        suggestion: 'Access API data through a hook from lib/hooks/ that returns a typed ViewModel.',
      })
    }
  }

  return createResult('Generated API Audit', issues, start)
}