# Money invariant: all paise fields must be integers


PAISE_FIELDS = ("amount_paise", "balance_paise", "principal_paise", "outstanding_paise")


def assert_all_paise_integers(data):
    """Fail if any float/None in paise fields."""
    for key, value in data.items():
        if key.endswith("_paise") or "paise" in key:
            if not isinstance(value, int) or value is None:
                raise AssertionError(f"{key}={value} is not integer paise")


def test_money_invariants():
    valid = {"amount_paise": 100, "balance_paise": 500, "principal_paise": 10000}
    assert_all_paise_integers(valid)  # Should pass
