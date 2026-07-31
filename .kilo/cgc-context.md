# CodeGraphContext Integration — Token-Efficient Retrieval

CodeGraphContext (CGC) is active and indexed for this repository. Use CGC tools to retrieve only the relevant code for any given task, avoiding full-file reads that waste tokens.

## Graph Schema

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
| `CONTAINS` | File or Module contains Function/Class nodes |
| `IMPORTS` | Module A imports Module B |
| `INHERITS` | Class A inherits from Class B |

**Critical**: Always use `CONTAINS` (not `DEFINED_IN`) for file-to-function/class relationships. Always use `CALLS` for call edges. Always use `IMPORTS` for import edges.

## When to use CGC tools

- **Finding specific functions or classes**: Use `find_code` with a keyword or name instead of grepping or reading entire files.
- **Understanding call relationships**: Use `analyze_code_relationships` to see who calls a function or what a class depends on — this returns a compact graph summary, not raw source.
- **Complex queries**: Use `execute_cypher_query` to run direct Cypher queries against the code graph for precise, targeted retrieval. Use `CONTAINS` for file membership checks and `CALLS` for call edges.
- **Switching context**: Use `switch_context` when working across multiple repositories or sub-projects.
- **Code health checks**: Use `find_dead_code` and `calculate_cyclomatic_complexity` to identify problematic code without reading full files.
- **Background indexing status**: Use `check_job_status` after triggering `add_code_to_graph` or `add_package_to_graph`.

## Command Delivery Template

When using CGC tools, package instructions in this exact format to minimize friction and avoid schema guessing:

```
[CGC-EXECUTION-DIRECTIVE]
- Target Objective: <what to find>
- Permitted Tools: <specific CGC tool names>
- Prohibited Actions: <what NOT to do>
- Expected Output Schema: <JSON structure>
```

**Example**:
```
[CGC-EXECUTION-DIRECTIVE]
- Target Objective: Find all callers of compute_emi_fixed across the repository
- Permitted Tools: CodeGraphContext_find_code, CodeGraphContext_analyze_code_relationships
- Prohibited Actions: NO read_file, NO cat, NO raw database CLI queries, NO Cypher queries until schema is validated
- Expected Output Schema: JSON list containing: caller_name, file_path, line_number
```

## Fallback Rule

If a graph query returns 0 results, follow this protocol — **do not loop blindly with refined Cypher queries**:

1. **Schema health check**: Run `list_indexed_repositories` to verify the target directory is indexed
2. **Validate node labels**: Cross-reference against the Graph Schema table above (use `CONTAINS`, not `DEFINED_IN`; use `CALLS`, not `CALLS_TO`)
3. **Use `find_code` as fallback**: If Cypher returns 0 results after label validation, switch to `find_code` with semantic search — this uses a different retrieval path and avoids graph schema friction
4. **Do NOT retry Cypher** without first verifying the repository is indexed and the labels are correct

## Token optimization rules

1. **Never read an entire file** when `find_code` or `analyze_code_relationships` can return the relevant snippet.
2. **Prefer `execute_cypher_query`** over reading source files when you need cross-file relationship data (callers, callees, inheritance chains).
3. **Use `switch_context`** before querying a different sub-project (e.g., `backend`, `frontend`, `servers`) to avoid mixing unrelated context in the query results.
4. **Keep Cypher queries focused** — request only the nodes and relationships you need, not the entire graph.
5. **Use `find_code` with fuzzy matching** (`fuzzy=true`) when the exact name is uncertain, but prefer exact names for precision and lower token cost.
6. **Check `list_indexed_repositories`** first if unsure whether a directory has been indexed by CGC.
7. **Always validate node labels** from the Graph Schema table before writing Cypher queries. No guessing — `find_code` first, then `execute_cypher_query` with verified labels.

## CGC Environment

- Database: FalkorDB (local) at `/home/vasantha/.codegraphcontext/global/db/falkordb`
- Watch process: Active — `/home/vasantha/.local/bin/cgc watch /home/vasantha/AI-Projects/ClariFin_OS`
- SCIP indexer: Enabled for Python and TypeScript
- Ignore dirs: `node_modules`, `venv`, `.venv`, `dist`, `build`, `target`, `out`, `.git`, `.idea`, `.vscode`, `__pycache__`, `public`, `mocks`, `servers`, `memory-bank`, `docs`, `test-results`, `playwright-report`, `coverage`, `.next`, `generated`, `.pytest_cache`, `.mypy_cache`

## Available CGC MCP Tools

- `find_code` — retrieve code snippets by keyword/name (limit: 50 results)
- `analyze_code_relationships` — analyze callers/callees/dependencies (limit: 50)
- `execute_cypher_query` — run Cypher queries against the code graph (limit: 100)
- `add_code_to_graph` — one-time add a folder to the graph (background job)
- `add_package_to_graph` — add a package to the graph (background job)
- `check_job_status` — check background job progress
- `switch_context` — switch active graph context
- `list_indexed_repositories` — list indexed repos
- `find_dead_code` — find potentially unused functions
- `calculate_cyclomatic_complexity` — calculate function complexity
- `find_most_complex_functions` — find the most complex functions
- `watch_directory` / `unwatch_directory` — manage directory watching
- `list_watched_paths` — list watched directories
- `visualize_graph_query` — generate a Neo4j visualization URL for a Cypher query
- `discover_codegraph_contexts` — discover .codegraphcontext folders
- `generate_report` — generate a codegraph report
- `get_repository_stats` — get repository statistics
- `load_bundle` — load a pre-indexed bundle
