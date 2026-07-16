# Active Context

## Change Confidence Pipeline (Completed)

### Changes Made (July 16, 2026)
- Created `docs/ARCHITECTURE_CONSTRAINTS.md` — immutable rulebook (207 lines)
- Created `docs/CODE_GENERATION_CONTRACT.md` — AI execution rules (180 lines)
- Created `docs/CHANGE_CONFIDENCE_PIPELINE.md` — staged validation approach (128 lines)
- Created `scripts/verify-change.sh` — orchestration wrapper for 3 verification levels
- Branch `stage-0-constraints-guardrails` updated and pushed

### Verification Levels
- **Level A**: Docs/config only → `scripts/verify-fast.sh`
- **Level B**: Affected capability → `scripts/verify-local.sh` with VERIFY_MODE=selective
- **Level C**: Full validation → `scripts/verify-local.sh` full pipeline

### Next Steps
- Proceed to next Stage 0 prompt
- Integrate SpendingWidget and MerchantWidget into dashboard/page.tsx

### OpenAPI Schema Exported (July 2026)
- 105 unique paths, 126 endpoints, 22 routers included