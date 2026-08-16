# CGC Precision Improvement Plan for Kilo

## Problem Statement

When Kilo uses CodeGraphContext (CGC) MCP tools for graph queries, it encounters schema/label friction:
- Wrong node labels and relationship types are guessed (e.g., `DEFINED_IN` instead of `CONTAINS`)
- Initial Cypher queries return 0 results, triggering trial-and-error loops
- No structured fallback protocol when queries fail
- `find_code` content matching returns large truncated snippets (~60K tokens) instead of focused results
- Token waste from schema discovery rounds instead of precise first-query hits

## Root Cause

The CGC graph schema uses specific node labels and relationship types that are not documented in the Kilo instruction file. The instruction file provides general guidance but lacks:
1. Exact graph schema map (node labels, relationship types, key properties)
2. A standardized command delivery template for structured CGC tool calls
3. A graph query fallback rule for when queries return empty results

## Actual CGC Graph Schema (Verified)

### Node Labels
| Label | Key Properties |
|---|---|
| `Function` | `name`, `path`, `line_number`, `args`, `class_context`, `context_type`, `cyclomatic_complexity`, `decorators`, `end_line`, `is_dependency`, `lang`, `source` |
| `Class` | `name`, `path`, `line_number` |
| `File` | `path` |
| `Module` | `name` |
| `Variable` | `name`, `path` |
| `Parameter` | `name` |
| `Interface` | `name`, `path` |
| `Directory` | `name` |
| `Repository` | `name` |
| `ExternalClass` | `name` |

### Relationship Types
| Type | Description |
|---|---|
| `CALLS` | Function A calls Function B |
| `HAS_PARAMETER` | Function has a Parameter node |
| `CONTAINS` | File/Module contains Function/Class nodes |
| `IMPORTS` | Module A imports Module B |
| `INHERITS` | Class A inherits from Class B |

## Changes Required

### 1. Update `.kilo/cgc-context.md` with Schema Map and Standardized Template

Add a `## Graph Schema` section documenting the exact node labels, relationship types, and key properties listed above.

Add a `## Command Delivery Template` section with the standardized format:

```
[CGC-EXECUTION-DIRECTIVE]
- Target Objective: <what to find>
- Permitted Tools: <specific CGC tool names>
- Prohibited Actions: <what NOT to do>
- Expected Output Schema: <JSON structure>
```

Add a `## Fallback Rule` section:

```
If a graph query returns 0 results:
1. Check repository is indexed: run `list_indexed_repositories`
2. Verify node labels match actual schema (use the Graph Schema table above)
3. Use `find_code` as a fallback (semantic search, not graph traversal)
4. Do NOT loop with refined Cypher queries without schema validation first
```

### 2. Update `.kilo/kilo.jsonc` with CGC Tool Result Limits

Add `MAX_TOOL_RESULT_TOKENS` and `TOOL_RESULT_LIMITS` to CGC MCP environment to prevent oversized responses that waste tokens. Current config already has these but should be verified.

### 3. Add `instructions` field in `kilo.jsonc` pointing to updated CGC context file

Already done - `.kilo/cgc-context.md` is referenced via `instructions` field.

## Validation Plan

1. Run a test query using `find_code` for a known function - verify it returns results on first attempt
2. Run a graph relationship query using the correct `CONTAINS` relationship type - verify non-zero results
3. Run a query with a wrong label - verify the fallback rule kicks in (use `find_code` instead of retrying Cypher)
4. Measure token savings: compare graph query response size vs full file read for `src/db.py`