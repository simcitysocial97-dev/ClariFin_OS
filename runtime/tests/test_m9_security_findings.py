"""M9 stabilization — the CodeQL findings, and what each was classified as.

CodeQL raised 30 open alerts against ``main``. Each one was classified as a
genuine defect (fixed), a validated false positive (narrow, justified
suppression), or a stale finding from a retired analysis (cleared by a real
re-analysis). This module pins the *defect* half of that classification: a
change that puts an exception message, a card number or a caller-controlled
segment back into a response or a log fails here, so the finding cannot be
reintroduced quietly between CodeQL runs.

The *suppression* half is pinned too — a suppression is only honest while the
code it excuses is still the code it was written against, so each one is
asserted to exist AND to sit on a line that still carries the guarded
expression.

Run:
    python -m pytest runtime/tests/test_m9_security_findings.py -q
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent

# CodeQL actions are pinned to an immutable 40-character commit SHA with the tag
# retained as a trailing comment, so matching on an `@v3` suffix would make
# these tests blind to the workflow. Match the action path and accept any
# immutable ref (tag or SHA) instead.
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _is_codeql_init(uses: str) -> bool:
    prefix = "github/codeql-action/init@"
    if not uses.startswith(prefix):
        return False
    ref = uses[len(prefix) :].split("#")[0].strip()
    return bool(ref) and (ref.startswith("v") or bool(_SHA_RE.match(ref)))


PY_ALERTS = {
    # py/path-injection — orchestrator.py x4, import_router.py x2. The alert is
    # reported at each site that TOUCHES the derived path, not at the one place
    # the guard is written, so a fix at a single site is not enough.
    "runtime/platform/ai/orchestrator.py": 5,
    "backend/src/routers/import_router.py": 4,
    # py/clear-text-logging-sensitive-data — 1 alert (:884); :618 was fixed
    "backend/src/extraction/metadata_extractor.py": 1,
    # py/clear-text-logging-sensitive-data (:172)
    "backend/src/ingest.py": 1,
    # py/stack-trace-exposure (:201)
    "backend/src/errors.py": 1,
}

JS_ALERTS = {
    "frontend/scripts/verify-mock-sync.ts": 1,
}


def _read(rel: str) -> str:
    return (REPO / rel).read_text()


# ---------------------------------------------------------------------------
# Genuine defects — fixed
# ---------------------------------------------------------------------------


def test_the_extractor_never_prints_a_full_card_number():
    """`py/clear-text-logging-sensitive-data` on metadata_extractor.py:884/618.

    The extractor logged `card={result['card_number']}` and every
    directPattern/proximity match with its raw value. Debug output is `print`,
    which lands in CI logs and terminal scrollback, both retained far longer
    than the process (CWE-532).
    """
    src = _read("backend/src/extraction/metadata_extractor.py")
    assert "result['card_number']}" not in src, "the summary log must not print the PAN"
    # Both match sites report the value they found; each reports it masked.
    assert (
        'f"{_mask_for_log(field_name, value)}"' in src
    ), "the directPattern match log must mask the value it found"
    assert (
        'f"{_mask_for_log(field_name, result)}"' in src
    ), "the proximity match log must mask the value it found"
    assert (
        "card=****{result['card_last4']}" in src
    ), "the summary log must report the masked card, not the PAN"


def test_the_masker_only_masks_account_identifiers():
    """The masker must not become a blanket censor, and must keep the last four."""
    import sys

    sys.path.insert(0, str(REPO / "backend"))
    try:
        from src.extraction.metadata_extractor import (  # noqa: PLC0415
            _mask_for_log,
        )
    finally:
        sys.path.pop(0)

    assert _mask_for_log("card_number", "4321 23XX XXXX 1234") == "****1234"
    assert _mask_for_log("pan", "1234567890123456") == "****3456"
    assert _mask_for_log("cvv", "123") == "****"
    # A field that is not an identifier is untouched.
    assert _mask_for_log("total_amount_due", 1234.5) == 1234.5
    assert _mask_for_log("due_date", "2026-04-01") == "2026-04-01"


def test_the_stage_summary_does_not_carry_the_exception_message():
    """`py/stack-trace-exposure` on import_router.py:63 (statement_orchestrator).

    `summary["*_error"] = str(e)` is returned from an API handler and persisted
    for audit, so an arbitrary exception message — filesystem paths, SQL
    fragments, driver text — reached the client (CWE-209, CWE-497).
    """
    src = _read("backend/src/orchestration/statement_orchestrator.py")
    assert not re.search(
        r'summary\["\w+_error"\]\s*=\s*str\(', src
    ), "a stage error is still the raw exception message"
    assert "logger.exception(" in src, "the detail must still reach the server log"
    assert "type(exc).__name__" in src
    # Every stage failure routes through the single helper.
    assert src.count("_stage_failure(") >= 7, "six stages plus the helper definition"


def test_csv_import_warnings_do_not_carry_the_exception_message():
    """`py/stack-trace-exposure` on import_router.py:103 (csv_importer)."""
    src = _read("backend/src/extraction/csv_importer.py")
    assert "Error processing - {str(e)}" not in src
    assert "Error processing - {type(e).__name__}" in src
    assert "logger.exception(" in src


def test_the_verification_write_error_reason_does_not_carry_the_exception_message():
    """`py/stack-trace-exposure` on platform.py:139 (verification_write).

    `decision_reason: str(exc)` sat in the result envelope, which platform
    handlers return from `_ok()` with a 200. The report_id is already logged
    and is enough to correlate.
    """
    src = _read("runtime/platform/api/services/verification_write.py")
    assert '"decision_reason": str(exc)' not in src
    assert '"decision_reason": f"internal error ({type(exc).__name__})"' in src


def test_the_contract_workflow_runs_without_a_write_scope():
    """`actions/untrusted-checkout/critical` on api-contracts.yml.

    The workflow is triggered by `workflow_run` on a failed Playwright run. It
    held `pull-requests: write` and used it for nothing.
    """
    wf = yaml.safe_load(_read(".github/workflows/api-contracts.yml"))
    perms = wf["permissions"]
    assert perms == {"contents": "read"}, (
        f"workflow_run + checkout of an untrusted ref with {perms} is the "
        "critical finding again"
    )


def test_no_workflow_checks_out_a_workflow_run_head_sha():
    """`actions/cache-poisoning/poisonable-step` on api-contracts.yml.

    Removing the write scope fixed the privilege leak, not the cache-poisoning
    path: the job still checked out `github.event.workflow_run.head_sha`, which
    a fork's pull request controls, and `bootstrap-runtime` restores a cache. A
    fork could seed that cache and have a later default-branch run restore it.

    For a `workflow_run` event `github.sha` is already the default branch's head,
    which is the trusted ref this gate exists to re-check, so the override is
    also simply wrong for the job's purpose.
    """
    offenders = []
    for path in sorted((REPO / ".github").rglob("*.yml")):
        text = path.read_text()
        # Only executable lines count; the reasoning comments name it on purpose.
        code = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )
        if "workflow_run" in code and "workflow_run.head_sha" in code:
            offenders.append(str(path.relative_to(REPO)))
    assert (
        not offenders
    ), f"workflows checking out an untrusted workflow_run head: {offenders}"


# ---------------------------------------------------------------------------
# Validated false positives — narrow, justified suppressions
# ---------------------------------------------------------------------------


def test_every_python_suppression_is_present_and_counted():
    """A suppression is only honest while the code it excuses still holds.

    Both the presence and the count are asserted: a silent deletion of a
    comment would let the alert return, and an added one would mean a new
    finding was waved through without a classification.
    """
    for rel, expected in PY_ALERTS.items():
        found = len(re.findall(r"#\s*codeql\[", _read(rel)))
        assert found == expected, (
            f"{rel} carries {found} codeql suppression comment(s), expected "
            f"{expected}. Each needs a classification; see "
            "runtime/tests/test_m9_security_findings.py."
        )


def test_every_python_suppression_sits_on_the_line_before_its_alert():
    """Python only reads a suppression comment placed on its OWN line.

    This is the failure the first pass made. Nine suppressions were written, six
    of them as trailing comments — the idiomatic placement in every other
    language — and CodeQL still reported five sites as live high-severity alerts
    on the pull request. The CodeQL changelog is explicit for Python:
    `codeql[query-id]` comments "must be placed on a blank line before the
    alert". The three that worked were the ones already written that way, by
    accident, because their justification was a paragraph rather than a trailing
    aside.

    A suppression that CodeQL silently ignores is worse than none: it reads like
    a decision and closes nothing.
    """
    for rel in PY_ALERTS:
        lines = _read(rel).splitlines()
        for index, line in enumerate(lines):
            match = re.search(r"#\s*codeql\[", line)
            if not match:
                continue
            assert line.strip().startswith("# codeql["), (
                f"{rel}:{index + 1} is a trailing comment. In Python a codeql "
                "suppression must be the whole comment, on the line before the "
                "alert — a trailing one is silently ignored."
            )
            following = [
                n.strip()
                for n in lines[index + 1 :]
                if n.strip() and not n.strip().startswith("#")
            ]
            assert following, f"{rel}:{index + 1} suppresses nothing below it"


def test_every_python_suppression_names_a_python_query():
    for rel in PY_ALERTS:
        for query in re.findall(r"#\s*codeql\[([^\]]+)\]", _read(rel)):
            assert query.startswith(
                "py/"
            ), f"{rel} suppresses {query!r} in Python source"


def test_the_js_suppression_names_the_reported_query():
    src = _read("frontend/scripts/verify-mock-sync.ts")
    assert "// codeql[js/incomplete-multi-character-sanitization]" in src
    # The value it excuses must still be RegExp-only: if it is ever used as a
    # filesystem path the false positive stops being one.
    normalised = src.split("const normalizedFile")[1].split(";")[0]
    assert "path" not in normalised
    for after in src.split("const normalizedFile")[1:]:
        head = after[: after.find("totalChecked++")]
        assert "readFile" not in head and "path.join" not in head, (
            "normalizedFile reached the filesystem — the suppression no longer "
            "applies"
        )


def test_the_vendored_bundle_exclusion_is_a_single_named_file():
    """`js/double-escaping` on the upstream pdf.js worker build.

    The file is part of the maintained artifact, so it is neither deleted nor
    edited; it is excluded by name. A directory or glob would quietly drop the
    hand-written code around it.
    """
    wf = yaml.safe_load(_read(".github/workflows/security-codeql.yml"))
    init = next(
        s for s in wf["jobs"]["analyze"]["steps"] if _is_codeql_init(s.get("uses", ""))
    )
    config = yaml.safe_load(init["with"]["config"])
    assert config["paths-ignore"] == ["frontend/public/pdf.worker.mjs"]
    assert (REPO / "frontend/public/pdf.worker.mjs").exists(), (
        "the excluded file is part of the served artifact and must not be "
        "deleted to make the finding go away"
    )


def test_the_default_codeql_setup_is_not_also_active():
    """Two owners for one language means two databases and two verdicts."""
    wf = yaml.safe_load(_read(".github/workflows/security-codeql.yml"))
    assert wf["jobs"]["analyze"]["name"] == "Analyze"
    langs = set(
        next(
            s
            for s in wf["jobs"]["analyze"]["steps"]
            if _is_codeql_init(s.get("uses", ""))
        )["with"]["languages"].split(", ")
    )
    assert langs == {
        "python",
        "javascript",
        "actions",
    }, "every security-relevant language must have exactly one owner"
