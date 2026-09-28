# M9-C50 Phase 0 — Initial Architecture Graph

**Generated:** 2026-09-04T11:11:00+00:00

Consolidated view of the verification control-plane architecture based on live inspection
(canonical surface, facade, executor pipeline, capability catalog, authority modules).

```mermaid
graph TD
  subgraph OperatorSurface
    CLI[verify.py thin shim]
    FACADE[control_plane_facade.py :: main]
    TREE[canonical_control_plane.py : 9-command tree + classification]
  end

  subgraph CanonicalAuthority
    REG[VerificationRegistry -> verification.yaml]
    CCR[CapabilityContractRegistry]
    CAPAUTH[capability_authority.assert_no_competing_authority]
    OBLIG[obligation.py : dispositions]
  end

  subgraph PlanExecute
    PLANNER[ControlPlanePlanner]
    EPLANNER[evidence_planner.py : PlannedTask]
    EPIPE[executor_pipeline.py : ADAPTERS x8]
    EXEC[ExecutionOrchestrator]
  end

  subgraph Evidence
    ECONTRACT[EvidenceContract / evidence_integrity]
    EREUSE[evidence_reuse.py]
    EVSTORE[event_store.py observability]
  end

  subgraph MutationForensic
    MUT[MutationOrchestrator]
    FORENSIC[forensic_cli.py / blast_radius_cli.py (legacy DEPRECATED)]
  end

  CLI --> FACADE
  FACADE --> TREE
  TREE --> CAPAUTH
  CAPAUTH --> REG
  REG --> CCR
  PLANNER --> REG
  PLANNER --> EPLANNER
  EPLANNER --> EPIPE
  EPIPE --> EXEC
  EXEC --> ECONTRACT
  ECONTRACT --> EREUSE
  ECONTRACT --> EVSTORE
  EXEC --> MUT
  MUT --> FORENSIC
  OBLIG --> EREUSE
```

## Structural Observations

1. **Single operator surface exists** — one thick facade, one thin shim, one command tree.
2. **Dormant legacy CLI** (`forensic_cli.py`, `blast_radius_cli.py`) remain reachable as DEPRECATED
   tokens; their delegation to a single canonical op is claimed but not yet exhaustively proven.
3. **Evidence contract shows drift** — capability catalog references evidence kinds absent from the
   closed `EVIDENCE_KINDS` vocabulary (10 issues).
4. **Planner→executor chain is now populated** for all 8 task kinds in the working tree.
5. **Obligation model** is centralized (`obligation.py`) with an explicit closed disposition set.