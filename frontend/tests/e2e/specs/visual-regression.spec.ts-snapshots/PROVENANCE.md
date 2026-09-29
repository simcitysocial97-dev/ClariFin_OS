# Visual Regression Baseline Provenance

The snapshots in this directory are **generated artifacts**, not source. They are
committed because the visual-regression suite is a required gate and has nothing
to compare against without them. They must only be replaced by a deliberate,
provenance-bound re-baselining run — never edited, never deleted to make a run
pass, and never re-recorded to hide a regression.

## Regeneration command

```bash
cd frontend
npx playwright test tests/e2e/specs/visual-regression.spec.ts \
  --project=chromium --update-snapshots
```

Then re-run **without** `--update-snapshots` and confirm the suite is green. A
regeneration that does not also pass a clean verification run has not produced a
baseline, it has produced a snapshot of a broken render.

## Recorded provenance

| Field | Value |
|---|---|
| Repository SHA (tree that was rendered) | `96ae2e649370c2b72078185080aa4d0f65142e31` |
| Playwright version | `1.63.0` |
| Browser | Chromium (`chromium-linux` snapshot suffix) |
| Platform | Linux, `chromium-linux` |
| Viewport | 1280x720 (set in `visual-regression.spec.ts` `beforeEach`) |
| Device scale factor | 1 (default) |
| Run (UTC) | 2026-09-29T05:43:41Z |
| Project | `chromium` |
| Verification run after regeneration | 24 passed |

## Why these were regenerated (2026-09-29)

The committed baselines were stale relative to the M9-C71 console work that had
already landed on `main`; 50 of the visual-regression test instances were failing
on `main` before this work started, while 6 (sidebar, header, upload button,
mode toggle, empty state, modal) still passed. A suite where some snapshots
match and others are far off is a stale-baseline signature, not a platform or
font mismatch — and the 6 passing ones are what establishes that this Linux
environment can reproduce the existing baselines at all.

The rendered tree also includes one behavioural change from this series: the
dashboard page no longer renders a second, superseded inline footer. The layout
mounts `PlatformFooterBar` (which owns `data-testid="platform-footer-bar"`), and
the old inline footer duplicated it, so `text=No AI` matched two elements and
failed Playwright's strict mode. `dashboard-page-*.png` therefore legitimately
shows one footer rather than two.

Diff ratios before regeneration ranged from 0.01 to 0.14 of all image pixels;
several exceeded the CI `threshold` of 0.01.

## Rules for future changes

- A snapshot diff is a signal, not noise. Investigate the cause before re-recording.
- If a change is intentional and correct, re-record **all** affected snapshots
  and record the provenance above.
- If a change is unintended, fix the code. Never re-record to make it pass.
- Do not relax `DIFF_THRESHOLD` or `MAX_DIFF_PIXELS` to accommodate a diff.
- Volatile readouts (cache counters, hit rates) are masked via
  `volatileRuntimeReadouts()`; if a new volatile readout appears, add a mask
  rather than re-recording.
