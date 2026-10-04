"""M10-R3 — the capability alias bridge, and proof the fail-closed control keeps its teeth.

`exec-0009` blocked every plan: the cross-layer impact planner names frontend
capabilities in a vocabulary the verification registry does not use, so six entries
resolved to nothing and tripped the fail-closed review obligation. It was reported as
`echo 'UNMAPPED capabilities …' && exit 1` — a registry fact expressed as a shell exit.

This file pins the two escape hatches that fixed it, and — more importantly — pins how
*narrow* they are, because a mapping broad enough to silence the gate would be worse than
the failure it fixed.
"""

from __future__ import annotations

import pytest

from runtime.foundation.verification.capability_resolver import (
    FRONTEND_CAPABILITY_PREFIX_ALIASES,
    PATH_CAPABILITY_BRIDGES,
    PLANNER_CAPABILITY_ALIASES,
    resolve_capability_alias,
)


class TestExactAliases:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("useLoansCapability", "loan-engine"),
            ("useAccountsCapability", "account-engine"),
            ("useBehaviourCapability", "behaviour-engine"),
            ("useCashflowCapability", "cashflow-engine"),
            ("useCreditCardsCapability", "credit-card-engine"),
            ("useNetWorthCapability", "balance-engine"),
            ("useReconciliationCapability", "reconciliation"),
            ("useForecastCapability", "frontend-verification"),
            ("useInvestmentsCapability", "frontend-verification"),
        ],
    )
    def test_every_hook_bridges(self, raw, expected):
        assert resolve_capability_alias(raw) == expected

    def test_a_verification_id_passes_through_untouched(self):
        assert resolve_capability_alias("account-engine") == "account-engine"


class TestConventionPrefix:
    @pytest.mark.parametrize(
        "raw",
        [
            "frontend:component:frontend-graph:investments",
            "frontend:frontend_dto_type:frontend-shared:forecast-view-model",
            "frontend:frontend_utility:frontend-shared:global-setup",
            "frontend:anything:at:all",
        ],
    )
    def test_the_frontend_namespace_bridges(self, raw):
        """`verification.yaml` declares frontend-verification's scope as "Frontend
        components and hooks verified by the frontend profile" — which covers every
        capability in that namespace by definition. So this is a statement of ownership,
        not a way of making the gate quiet."""
        assert resolve_capability_alias(raw) == "frontend-verification"

    def test_it_claims_nothing_outside_the_namespace(self):
        """The narrowness that matters. A prefix bridge that matched loosely would
        swallow genuinely unmapped capabilities, which is the exact failure the
        fail-closed obligation exists to catch."""
        for raw in (
            "backend:component:something",
            "some-unknown-capability",
            "UNMAPPED:backend/src/newthing.py",
            "frontendish-thing",
            "",
        ):
            assert (
                resolve_capability_alias(raw) == raw
            ), f"{raw!r} must not be silently claimed by a frontend bridge"

    def test_the_namespace_is_declared_not_inferred(self):
        assert FRONTEND_CAPABILITY_PREFIX_ALIASES == (
            ("frontend:", "frontend-verification"),
        )


class TestPathBridges:
    def test_the_e2e_config_is_bridged(self):
        assert PATH_CAPABILITY_BRIDGES["frontend/playwright.config.ts"] == "e2e-tests"

    def test_it_is_exact_not_a_glob(self):
        """A glob would claim every future config file automatically.

        The whole point of the fail-closed obligation is that a NEW unclaimed file must be
        reviewed rather than assumed safe, so the table stays literal.
        """
        assert "*" not in repr(PATH_CAPABILITY_BRIDGES)
        assert all("/" in k for k in PATH_CAPABILITY_BRIDGES)
        assert (
            len(PATH_CAPABILITY_BRIDGES) == 2
        ), "a new entry must be a deliberate decision with a named owner"


class TestTheControlIsNotSilenced:
    """The mapping must not have turned the gate off.

    `exec-0009` firing on every plan was the *symptom*. The cause was six entries with no
    verification owner. Mapping them removes the symptom only if they genuinely have one;
    the guard below is what stops "map everything" from being the answer.
    """

    def test_the_alias_table_is_small_and_enumerated(self):
        assert len(PLANNER_CAPABILITY_ALIASES) == 9, (
            "every alias is a named frontend hook mapped to a named engine or to "
            "frontend-verification; a large jump here means something started guessing"
        )

    def test_every_alias_target_is_a_real_capability(self):
        from runtime.foundation.verification.registry import get_registry

        registry = get_registry()
        registry.load()
        known = {c.id for c in registry.get_all_capabilities()}
        for raw, target in PLANNER_CAPABILITY_ALIASES.items():
            assert target in known, f"{raw} maps to unknown capability {target!r}"
        for _, target in FRONTEND_CAPABILITY_PREFIX_ALIASES:
            assert target in known
        for path, target in PATH_CAPABILITY_BRIDGES.items():
            assert target in known, f"{path} maps to unknown capability {target!r}"

    def test_an_unbridged_entry_is_left_for_the_gate_to_catch(self):
        """The resolver returns the input unchanged, which is what the caller treats as
        unmapped. This is the line the fail-closed obligation stands on."""
        assert (
            resolve_capability_alias("a-capability-nobody-has-heard-of")
            == "a-capability-nobody-has-heard-of"
        )
