"""
Unit tests for Money domain model.

Tests cover all arithmetic, comparison, and conversion operations
on the Money class, which represents monetary values in integer paise.
"""

import pytest

from src.core.domain.money import Money

# ============================================================================
# Construction
# ============================================================================


class TestMoneyConstruction:
    """Money must be created with integer paise."""

    def test_creates_from_integer_paise(self) -> None:
        """Money(100) should create a valid instance."""
        m = Money(100)
        assert m.paise == 100

    def test_raises_typeerror_for_float_paise(self) -> None:
        """Money(1.5) should raise TypeError — paise must be int."""
        with pytest.raises(TypeError, match="integer paise"):
            Money(1.5)  # type: ignore[arg-type]

    def test_raises_typeerror_for_string_paise(self) -> None:
        """Money("100") should raise TypeError — paise must be int."""
        with pytest.raises(TypeError, match="integer paise"):
            Money("100")  # type: ignore[arg-type]

    def test_creates_zero(self) -> None:
        """Money(0) should create a valid zero-money instance."""
        m = Money(0)
        assert m.paise == 0
        assert m.is_zero()

    def test_creates_negative(self) -> None:
        """Money(-500) should create a valid negative instance."""
        m = Money(-500)
        assert m.paise == -500
        assert m.is_negative()

    def test_from_rupees_integer(self) -> None:
        """from_rupees(100) should create Money(10000)."""
        m = Money.from_rupees(100)
        assert m.paise == 10000

    def test_from_rupees_float(self) -> None:
        """from_rupees(123.45) should create Money(12345)."""
        m = Money.from_rupees(123.45)
        assert m.paise == 12345

    def test_from_rupees_rounding(self) -> None:
        """from_rupees should round to nearest paise."""
        m = Money.from_rupees(0.335)
        assert m.paise == 34  # round(0.335 * 100) = round(33.5) = 34

    def test_to_rupees(self) -> None:
        """to_rupees() should convert paise back to float rupees."""
        m = Money(12345)
        assert m.to_rupees() == 123.45

    def test_to_rupees_negative(self) -> None:
        """to_rupees() should work for negative amounts."""
        m = Money(-5000)
        assert m.to_rupees() == -50.0


# ============================================================================
# Arithmetic Operations
# ============================================================================


class TestMoneyArithmetic:
    """All arithmetic operations return new Money instances."""

    def test_add(self) -> None:
        """add should sum two Money values."""
        result = Money(100).add(Money(50))
        assert result.paise == 150

    def test_add_operator(self) -> None:
        """+ operator should sum two Money values."""
        result = Money(100) + Money(50)
        assert result.paise == 150

    def test_add_negative(self) -> None:
        """add with negative should reduce the value."""
        result = Money(100).add(Money(-30))
        assert result.paise == 70

    def test_add_typeerror(self) -> None:
        """add with non-Money should raise TypeError."""
        with pytest.raises(TypeError, match="Cannot add Money"):
            Money(100).add(50)  # type: ignore[arg-type]

    def test_subtract(self) -> None:
        """subtract should return the difference."""
        result = Money(100).subtract(Money(30))
        assert result.paise == 70

    def test_subtract_operator(self) -> None:
        """- operator should return the difference."""
        result = Money(100) - Money(30)
        assert result.paise == 70

    def test_subtract_negative_result(self) -> None:
        """subtract should allow negative results."""
        result = Money(30).subtract(Money(100))
        assert result.paise == -70

    def test_subtract_typeerror(self) -> None:
        """subtract with non-Money should raise TypeError."""
        with pytest.raises(TypeError, match="Cannot subtract"):
            Money(100).subtract(30)  # type: ignore[arg-type]

    def test_multiply_by_int(self) -> None:
        """multiply should scale by integer factor."""
        result = Money(100).multiply(3)
        assert result.paise == 300

    def test_multiply_operator(self) -> None:
        """* operator should scale by integer factor."""
        result = Money(100) * 3
        assert result.paise == 300

    def test_rmul_operator(self) -> None:
        """reflected * operator should work (3 * Money(100))."""
        result = 3 * Money(100)
        assert result.paise == 300

    def test_multiply_by_zero(self) -> None:
        """multiply by zero should return zero Money."""
        result = Money(100).multiply(0)
        assert result.paise == 0

    def test_multiply_negative(self) -> None:
        """multiply by negative should negate the value."""
        result = Money(100).multiply(-2)
        assert result.paise == -200

    def test_multiply_typeerror(self) -> None:
        """multiply with non-int should raise TypeError."""
        with pytest.raises(TypeError, match="multiplied by int"):
            Money(100).multiply(1.5)  # type: ignore[arg-type]

    def test_divide_by_int(self) -> None:
        """divide should split by integer divisor (rounded)."""
        result = Money(100).divide(3)
        assert result.paise == 33  # round(100/3) = round(33.33) = 33

    def test_divide_operator(self) -> None:
        """/ operator should split by integer divisor."""
        result = Money(100) / 3
        assert result.paise == 33

    def test_divide_exact(self) -> None:
        """divide should give exact result when divisible."""
        result = Money(100).divide(4)
        assert result.paise == 25

    def test_divide_by_zero(self) -> None:
        """divide by zero should raise ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError, match="Cannot divide Money by zero"):
            Money(100).divide(0)

    def test_divide_typeerror(self) -> None:
        """divide with non-int should raise TypeError."""
        with pytest.raises(TypeError, match="divided by int"):
            Money(100).divide(2.0)  # type: ignore[arg-type]

    def test_percentage(self) -> None:
        """percentage(25) should return 25% of the amount."""
        result = Money(10000).percentage(25)
        assert result.paise == 2500

    def test_percentage_zero(self) -> None:
        """percentage(0) should return zero Money."""
        result = Money(10000).percentage(0)
        assert result.paise == 0

    def test_percentage_hundred(self) -> None:
        """percentage(100) should return the full amount."""
        result = Money(10000).percentage(100)
        assert result.paise == 10000

    def test_percentage_rounding(self) -> None:
        """percentage should round correctly for odd amounts."""
        result = Money(10).percentage(33)
        assert result.paise == 3  # round(10 * 33 / 100) = round(3.3) = 3

    def test_percentage_typeerror(self) -> None:
        """percentage with non-int should raise TypeError."""
        with pytest.raises(TypeError, match="Percentage must be int"):
            Money(100).percentage(25.0)  # type: ignore[arg-type]

    def test_percentage_out_of_range(self) -> None:
        """percentage with value > 100 should raise ValueError."""
        with pytest.raises(ValueError, match="Percentage must be 0-100"):
            Money(100).percentage(150)

    def test_percentage_negative(self) -> None:
        """percentage with negative value should raise ValueError."""
        with pytest.raises(ValueError, match="Percentage must be 0-100"):
            Money(100).percentage(-10)

    def test_negate(self) -> None:
        """negate should flip the sign."""
        result = Money(100).negate()
        assert result.paise == -100

    def test_negate_operator(self) -> None:
        """unary - operator should flip the sign."""
        result = -Money(100)
        assert result.paise == -100

    def test_negate_negative(self) -> None:
        """negate of negative should become positive."""
        result = Money(-50).negate()
        assert result.paise == 50

    def test_absolute(self) -> None:
        """absolute should return positive value."""
        result = Money(-100).absolute()
        assert result.paise == 100

    def test_absolute_operator(self) -> None:
        """abs() should return positive value."""
        result = abs(Money(-100))
        assert result.paise == 100

    def test_absolute_positive(self) -> None:
        """absolute of positive should stay positive."""
        result = Money(100).absolute()
        assert result.paise == 100

    def test_absolute_zero(self) -> None:
        """absolute of zero should be zero."""
        result = Money(0).absolute()
        assert result.paise == 0


# ============================================================================
# Comparison Operations
# ============================================================================


class TestMoneyComparison:
    """Comparison methods and operators."""

    def test_is_zero_true(self) -> None:
        """is_zero should return True for Money(0)."""
        assert Money(0).is_zero()

    def test_is_zero_false(self) -> None:
        """is_zero should return False for non-zero."""
        assert not Money(1).is_zero()

    def test_is_positive_true(self) -> None:
        """is_positive should return True for positive amounts."""
        assert Money(100).is_positive()

    def test_is_positive_false(self) -> None:
        """is_positive should return False for zero."""
        assert not Money(0).is_positive()

    def test_is_positive_negative(self) -> None:
        """is_positive should return False for negative amounts."""
        assert not Money(-1).is_positive()

    def test_is_negative_true(self) -> None:
        """is_negative should return True for negative amounts."""
        assert Money(-100).is_negative()

    def test_is_negative_false(self) -> None:
        """is_negative should return False for zero."""
        assert not Money(0).is_negative()

    def test_is_negative_positive(self) -> None:
        """is_negative should return False for positive amounts."""
        assert not Money(1).is_negative()

    def test_equals_same(self) -> None:
        """equals should return True for equal amounts."""
        assert Money(100).equals(Money(100))

    def test_equals_different(self) -> None:
        """equals should return False for different amounts."""
        assert not Money(100).equals(Money(200))

    def test_equals_non_money(self) -> None:
        """equals should return False for non-Money types."""
        assert not Money(100).equals(100)  # type: ignore[arg-type]

    def test_compare_equal(self) -> None:
        """compare should return 0 for equal amounts."""
        assert Money(100).compare(Money(100)) == 0

    def test_compare_less(self) -> None:
        """compare should return -1 when self < other."""
        assert Money(50).compare(Money(100)) == -1

    def test_compare_greater(self) -> None:
        """compare should return 1 when self > other."""
        assert Money(100).compare(Money(50)) == 1

    def test_compare_typeerror(self) -> None:
        """compare with non-Money should raise TypeError."""
        with pytest.raises(TypeError, match="Cannot compare Money"):
            Money(100).compare(50)  # type: ignore[arg-type]

    def test_eq_operator(self) -> None:
        """== operator should compare amounts."""
        assert Money(100) == Money(100)
        assert Money(100) != Money(200)

    def test_eq_non_money(self) -> None:
        """== with non-Money should return NotImplemented (False)."""
        assert Money(100) != 100

    def test_lt_operator(self) -> None:
        """< operator should compare amounts."""
        assert Money(50) < Money(100)
        assert not (Money(100) < Money(50))

    def test_lt_non_money(self) -> None:
        """< with non-Money should return NotImplemented."""
        with pytest.raises(TypeError):
            _ = Money(100) < 50  # type: ignore[operator]

    def test_le_operator(self) -> None:
        """<= operator should compare amounts."""
        assert Money(50) <= Money(100)
        assert Money(100) <= Money(100)
        assert not (Money(100) <= Money(50))

    def test_le_non_money(self) -> None:
        """<= with non-Money should return NotImplemented."""
        with pytest.raises(TypeError):
            _ = Money(100) <= 50  # type: ignore[operator]

    def test_gt_operator(self) -> None:
        """> operator should compare amounts."""
        assert Money(100) > Money(50)
        assert not (Money(50) > Money(100))

    def test_gt_non_money(self) -> None:
        """> with non-Money should return NotImplemented."""
        with pytest.raises(TypeError):
            _ = Money(100) > 50  # type: ignore[operator]

    def test_ge_operator(self) -> None:
        """>= operator should compare amounts."""
        assert Money(100) >= Money(50)
        assert Money(100) >= Money(100)
        assert not (Money(50) >= Money(100))

    def test_ge_non_money(self) -> None:
        """>= with non-Money should return NotImplemented."""
        with pytest.raises(TypeError):
            _ = Money(100) >= 50  # type: ignore[operator]

    def test_hash_equal_money(self) -> None:
        """Equal Money instances should have equal hashes."""
        assert hash(Money(100)) == hash(Money(100))

    def test_hash_different_money(self) -> None:
        """Different Money instances should have different hashes."""
        assert hash(Money(100)) != hash(Money(200))

    def test_hash_used_in_set(self) -> None:
        """Money should work as a set element."""
        s = {Money(100), Money(200), Money(100)}
        assert len(s) == 2


# ============================================================================
# String Representation
# ============================================================================


class TestMoneyString:
    """String and format methods."""

    def test_str_contains_rupee_symbol(self) -> None:
        """__str__ should include ₹ and paise."""
        s = str(Money(12345))
        assert "₹" in s
        assert "12345" in s

    def test_repr_contains_paise(self) -> None:
        """__repr__ should show the constructor form."""
        r = repr(Money(12345))
        assert "Money" in r
        assert "paise=12345" in r

    def test_format_rupees(self) -> None:
        """format with 'rupees' spec should show INR format."""
        result = f"{Money(12345):rupees}"
        assert "₹" in result
        assert "123.45" in result

    def test_format_paise(self) -> None:
        """format with 'paise' spec should show paise."""
        result = f"{Money(12345):paise}"
        assert "12345 paise" in result

    def test_format_default(self) -> None:
        """format with no spec should match __str__."""
        result = f"{Money(12345)}"
        assert "₹" in result
        assert "12345" in result


# ============================================================================
# Edge Cases
# ============================================================================


class TestMoneyEdgeCases:
    """Boundary and edge case behavior."""

    def test_large_values(self) -> None:
        """Money should handle large paise values (₹10 crore)."""
        m = Money(10_00_00_00_000)  # ₹10 crore
        assert m.paise == 10_00_00_00_000

    def test_arithmetic_chain(self) -> None:
        """Chained arithmetic should produce correct result."""
        result = Money(1000).add(Money(500)).subtract(Money(200)).multiply(2)
        assert result.paise == 2600  # (1000 + 500 - 200) * 2

    def test_immutability(self) -> None:
        """Arithmetic should not modify the original Money."""
        original = Money(100)
        original.add(Money(50))
        assert original.paise == 100  # unchanged

    def test_division_rounding_half_up(self) -> None:
        """divide should round to nearest integer (banker's rounding not required)."""
        # round(5/2) = round(2.5) = 2 in Python 3
        result = Money(5).divide(2)
        assert result.paise == 2
