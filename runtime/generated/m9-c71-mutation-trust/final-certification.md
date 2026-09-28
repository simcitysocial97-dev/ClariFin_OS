# M9-C71 — Mutation Measurement Trust & Survivor Forensics

**Recorded:** 2026-09-28T00:15:26.632226+00:00
**HEAD:** `6319f89b1ce94b4fb62366403fa9a41ca905f74f`
**Tree:** `5df6f84bd126b57dea9c4eafa4edf4df1c915fa2`

## Certification

```text
MUTATION_MEASUREMENT_VALID = true
MUTATION_DISPATCH_VALID = true
MUTANT_EXECUTION_PROVEN = true
UNKNOWN_SURVIVORS = 0
RAW_SCORE = 79.1
EFFECTIVE_SCORE = 79.1
RAW_GATE = FAIL
```

## Raw (immutable evidence)

- population: 16904
- killed: 13361
- survived: 3532
- score: 79.1%

## Certified (evidence-adjusted, never replacing raw)

- valid population: 16886
- proven equivalent: 18
- proven unobservable: 0
- proven not reached: 0
- proven defensive: 0
- remaining real survivors: 3714
- effective score: 79.1%

## Canary

- KNOWN_KILL_MUTANT: **KILLED**
- KNOWN_SURVIVOR_MUTANT: **SURVIVED**
- KNOWN_REACHED_LOCATION: **REACHED**
- KNOWN_UNREACHED_LOCATION: **UNREACHED**

## Refusals

- none — the measurement is self-consistent

## Threshold

The gate remains **80%** and was not changed. `RAW_GATE` and `EFFECTIVE_GATE` are reported separately; an effective score above the threshold never redefines the raw gate.
