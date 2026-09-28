# M9-C71 — Mutation Measurement Trust & Survivor Forensics

**Recorded:** 2026-09-28T03:16:51.561786+00:00
**HEAD:** `4f9d3162e3212f2137e5cda9c89a42dcebcb287f`
**Tree:** `79a43f88bd76857b9cca7a51c54b62833ccbd026`

## Certification

```text
MUTATION_MEASUREMENT_VALID = true
MUTATION_DISPATCH_VALID = true
MUTANT_EXECUTION_PROVEN = true
UNKNOWN_SURVIVORS = 0
RAW_SCORE = 80.1
EFFECTIVE_SCORE = 80.1
RAW_GATE = PASS
```

## Raw (immutable evidence)

- population: 16904
- killed: 13534
- survived: 3359
- score: 80.1%

## Certified (evidence-adjusted, never replacing raw)

- valid population: 16886
- proven equivalent: 18
- proven unobservable: 0
- proven not reached: 0
- proven defensive: 0
- remaining real survivors: 3541
- effective score: 80.1%

## Canary

- KNOWN_KILL_MUTANT: **KILLED**
- KNOWN_SURVIVOR_MUTANT: **SURVIVED**
- KNOWN_REACHED_LOCATION: **REACHED**
- KNOWN_UNREACHED_LOCATION: **UNREACHED**

## Refusals

- none — the measurement is self-consistent

## Threshold

The gate remains **80%** and was not changed. `RAW_GATE` and `EFFECTIVE_GATE` are reported separately; an effective score above the threshold never redefines the raw gate.
