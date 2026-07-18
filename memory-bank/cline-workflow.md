# Cline Workflow

## Tool Selection Model

The workflow selects tools based on information type, not fixed order.

### Semantic Questions → CGC
- Finding definitions, classes, functions, interfaces
- Understanding module structure and architecture
- Tracing dependency relationships
- Symbol source retrieval

### Lexical Questions → rg
- Imports, references, usages
- Decorators, configuration values, strings
- Exact symbol occurrences, test discovery

### Hybrid Questions → CGC + rg
- Caller/usages questions: Try CGC first, validate with rg if incomplete

---

## Discovery Phase (No File Reads)

1. Read `memory-bank/*.md` for known patterns
2. Use CGC for semantic questions
3. Use `rg` for lexical questions
4. For caller analysis: CGC attempt → rg validation if incomplete
5. Never use `read_file` for repository exploration

---

## Modification Phase (Targeted File Reads)

1. Use `read_file` only for files already identified in discovery
2. Make targeted edits
3. Run verification

---

## Decision Examples

**Example A:** "Where is UserService class?" → CGC `find_code`

**Example B:** "Who imports UserService?" → `rg "UserService" --type ts`

**Example C:** "What calls processTransaction?" → CGC attempt → rg validation if incomplete

---

## After Code Changes

1. Run `verify-fast.sh`
2. Fix all failures
3. Run `verify-local.sh` for behavioural changes