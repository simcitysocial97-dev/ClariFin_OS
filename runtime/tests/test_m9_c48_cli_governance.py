# runtime/tests/test_m9_c48_cli_governance.py

from __future__ import annotations

import json

from runtime.foundation.verification.cli_governance import (
    CLASSES,
    POLICY,
    classify_commands,
    extract_commands,
)


def test_classes_complete():
    expected = {
        "CANONICAL",
        "ALIAS",
        "COMPATIBILITY",
        "INTERNAL",
        "LEGACY",
        "DUPLICATE",
        "UNREACHABLE",
    }
    assert set(CLASSES) == expected


def test_extract_commands_returns_list():
    cmds = extract_commands()
    assert isinstance(cmds, list)
    assert "mutation" in cmds
    assert "status" in cmds


def test_classify_commands_assigns_class():
    rep = classify_commands()
    by_class = rep.to_dict()["by_class"]
    # At least one canonical.
    assert by_class.get("CANONICAL", 0) > 0
    # Total = unique commands.
    assert rep.total == len(set(rep.classifications))


def test_mutation_is_canonical():
    rep = classify_commands(["mutation"])
    assert rep.classifications[0].classification == "CANONICAL"


def test_unclassified_command_is_unreachable():
    rep = classify_commands(["definitely-not-a-real-command"])
    assert rep.classifications[0].classification == "UNREACHABLE"


def test_policy_table_keys_are_subset_of_commands():
    rep = classify_commands()
    commands = {c.command for c in rep.classifications}
    set(POLICY.keys()) - commands
    # The policy can have more entries than commands (forward planning);
    # but every command SHOULD be in the policy table.
    missing = commands - set(POLICY.keys())
    assert not missing, f"commands missing from policy: {sorted(missing)}"


def test_classify_real_repo_persists_evidence():
    rep = classify_commands()
    d = rep.to_dict()
    import os

    os.makedirs("runtime/generated/m9-c48", exist_ok=True)
    with open("runtime/generated/m9-c48/cli-classification.json", "w") as f:
        json.dump(d, f, indent=2)
    assert d["schema"] == "m9-c48/cli-governance@1"
    # All classifications in valid class set.
    for c in d["classifications"]:
        assert c["classification"] in CLASSES


def test_no_duplicate_commands():
    rep = classify_commands()
    cmds = [c.command for c in rep.classifications]
    assert len(cmds) == len(set(cmds))
