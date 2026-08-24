# AGENTS.md — ClariFin_OS

## Canonical Python Environment (MANDATORY)

The **ONLY** sanctioned Python environment is the repository-root virtualenv:

```
.venv/bin/python      # interpreter
.venv/bin/pytest      # pytest
.venv/bin/mutmut      # mutmut (pinned 3.7.0)
.venv/bin/coverage
```

### Rules for ALL terminal commands

1. **Always** run Python commands through the root `.venv`. From the repo root, prefer:

   ```bash
   .venv/bin/python runtime/verify.py ...
   .venv/bin/python -m pytest ...
   ```

   OR activate it first for a shell session:

   ```bash
   source .venv/bin/activate
   ```

2. **NEVER** create, use, or rely on a `backend/venv` or `backend/.venv`.
   Those are forbidden shadow environments (root cause of M9-C42.5 toolchain drift).

3. **NEVER** install packages with a bare system `pip3`/`python3 -m pip` without
   the `.venv` active. Dependency authority: root `pyproject.toml` →
   `pip install -e ".[all]"` **inside `.venv`**.

4. If `.venv` is missing or broken, recreate it with:

   ```bash
   bash scripts/bootstrap.sh      # builds .venv + installs root pyproject.toml [all]
   ```

5. Verify the environment before mutation/CI-sensitive work:

   ```bash
   .venv/bin/python runtime/verify.py env-check     # machine-readable fingerprint
   bash scripts/env-doctor.sh                       # environment diagnostic guard
   ```

### CI note

GitHub Actions installs the same dependency contract (`pip install -e ".[all]"`)
and exposes tools on PATH; `runtime/foundation/verification/env.py` resolves
`.venv/bin` first then PATH, so local `.venv` usage yields identical tooling
locally and in CI.

## Verification Runtime Commands

Use `python runtime/verify.py` (inside `.venv`) for platform verification:

- `runtime/verify.py status | metrics | history | deps | verify-status | integrity`
- `runtime/verify.py env-check` — canonical environment check
- `runtime/verify.py mutation --smoke` — bounded mutation infra smoke
- `runtime/verify.py mutation` — authoritative full campaign (CI only)

**Do NOT** run the full mutation campaign locally during debugging milestones.

## Key Decisions (context, not instruction)

- Repository-root `.venv` is the single Python environment (M9-C42.5 root-cause fix).
- mutmut pinned to 3.7.0 (root `pyproject.toml`); removed from `backend/requirements-dev.txt`
  to avoid dual-toolchain drift.
- Save all milestone artifacts under `runtime/generated/`.
- Existing test baseline: 315 tests; 4 pre-existing Earnd app failures are unrelated
  branch detections (`docker-compose down` needed to free ports).
