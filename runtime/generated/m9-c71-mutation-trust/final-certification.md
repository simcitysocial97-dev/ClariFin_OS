# M9-C71 — Mutation Measurement Trust & Survivor Forensics

**Recorded:** 2026-09-27T13:33:23.052655+00:00
**HEAD:** `dacfa2d4d9a3fcf250261568a10cd6a0eca22560`
**Tree:** `a111e944e3866cc6dfb0532864bf48173e2a3109`

## Certification

```text
MUTATION_MEASUREMENT_VALID = true
MUTATION_DISPATCH_VALID = true
MUTANT_EXECUTION_PROVEN = true
UNKNOWN_SURVIVORS = 0
RAW_SCORE = 77.2
EFFECTIVE_SCORE = 115.5
RAW_GATE = FAIL
```

## Raw (immutable evidence)

- population: 4150
- killed: 3202
- survived: 940
- score: 77.2%

## Certified (evidence-adjusted, never replacing raw)

- valid population: 2772
- proven equivalent: 0
- proven unobservable: 0
- proven not reached: 1378
- proven defensive: 0
- remaining real survivors: 0
- effective score: 115.5%

## Canary

- KNOWN_KILL_MUTANT: **KILLED**
- KNOWN_SURVIVOR_MUTANT: **SURVIVED**
- KNOWN_REACHED_LOCATION: **REACHED**
- KNOWN_UNREACHED_LOCATION: **UNREACHED**

## Refusals

- none — the measurement is self-consistent

## Threshold

The gate remains **80%** and was not changed. `RAW_GATE` and `EFFECTIVE_GATE` are reported separately; an effective score above the threshold never redefines the raw gate.
