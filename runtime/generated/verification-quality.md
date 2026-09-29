# Verification Quality Report — Program 7B.5

Generated: 2026-08-04

| Metric                | Value |
| --------------------- | ----: |
| Blast Radius Accuracy |  100% |
| False Positive Rate   |    0% |
| False Negative Rate   |    0% |
| Snapshot Stability    |  PASS |
| Planner Determinism   |  PASS |
| Report Determinism    |  PASS |
| Average Planning Time | 0.04 ms |
| Cache Hit Time        |  0.06 ms |

## Test Summary

| Category               | Count |
| ---------------------- | ----: |
| Total Runtime Tests    |    51 |
| Planner Tests          |     8 |
| Orchestrator Tests     |     8 |
| Evidence Tests         |     7 |
| Snapshot Tests         |     3 |
| False Positive Tests   |     4 |
| False Negative Tests   |     5 |
| Performance Tests      |     5 |

## Fixture Coverage

| Fixture                          | Scenario                        |
| -------------------------------- | ------------------------------- |
| loan_dto_field_rename            | DTO field rename blast radius   |
| endpoint_removed                 | API endpoint removal            |
| capability_mapper_mismatch       | Capability/mapper sync check    |
| workspace_registration_missing   | Workspace registration removal  |
| router_service_disconnect        | Router-service disconnect       |
| graph_renderer_disconnect        | Graph renderer removal          |
| baseline                         | No-change determinism baseline  |

## Performance Metrics

| Phase             | Time (ms) |
| ----------------- | --------: |
| Planner           |   0.04 |
| Orchestrator      |  14.08 |
| Evidence          |   18.94 |
| Report            |    4.43 |
| Cache             |     0.06 |

## Verification Health

- **All runtime tests pass:** PASS
- **Snapshots stable:** PASS
- **False positive rate = 0%:** PASS
- **False negative rate = 0%:** PASS
- **Performance within budget:** PASS
- **No application files modified:** PASS
- **No frontend regressions:** PASS
- **No backend regressions:** PASS
