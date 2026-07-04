"""
Financial Money Utilities — Single Authoritative Primitive Layer
================================================================

All monetary operations in ClariFin_OS must route through this module.
No inline conversions, no float arithmetic, no mixed rounding.

Design:
  - Internal representation: Decimal (exact)
  - Storage representation: int paise (1 rupee = 100 paise)
  - Rounding policy: ROUND_HALF_UP (banking standard)
  - Scale: 0 (paise is base unit, no fractional paise)

Rules:
  1. NEVER use float for money
  2. NEVER do inline v * 100 or int(v * 100)
  3. ALWAYS use to_paise() for Decimal→int conversion
  4. ALWAYS use from_paise() for int→Decimal conversion (display only)
  5. ALWAYS use Decimal for intermediate calculations
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union

# ============================================================
# Constants
# ============================================================

PAISE_PER_RUPEE = 100
ROUNDING_POLICY = ROUND_HALF_UP
PAISE_SCALE = 0  # paise is indivisible base unit

# Decimal context for financial calculations
# quantize uses this for rounding
_FINANCIAL_CTX = Decimal('0.01')  # 2 decimal places for rupee display


# ============================================================
# Core Conversions
# ============================================================

def to_paise(value: Union[Decimal, int, str]) -> int:
    """
    Convert any monetary amount to integer paise.
    
    This is the ONLY authorized conversion from Decimal/int/str → paise.
    
    Args:
        value: Amount as Decimal, int (rupees), or str (rupees)
               Floats are REJECTED — use Decimal(str(v)) instead.
    
    Returns:
        Integer paise amount (1 rupee = 100 paise)
    
    Raises:
        ValueError: If value is a float
        TypeError: If value type is unsupported
    
    Examples:
        >>> to_paise(Decimal('100.50'))
        10050
        >>> to_paise(100)
        10000
        >>> to_paise('1,234.56')
        123456
        >>> to_paise(Decimal('99.995'))
        10000  # ROUND_HALF_UP: 99.995 → 100.00 → 10000 paise
    
    Policy:
        - ROUND_HALF_UP at paise boundary
        - Negative values preserved
        - Zero returns 0
    """
    if isinstance(value, float):
        # Convert via Decimal to avoid IEEE 754 rounding errors
        value = Decimal(str(value))
    
    if isinstance(value, int):
        # Assume rupees
        return value * PAISE_PER_RUPEE
    
    if isinstance(value, str):
        # Clean string and convert to Decimal
        cleaned = value.replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').strip()
        if not cleaned or cleaned == '-':
            return 0
        decimal_val = Decimal(cleaned)
        return _round_to_paise(decimal_val)
    
    if isinstance(value, Decimal):
        return _round_to_paise(value)
    
    raise TypeError(
        f"Unsupported type {type(value)} for to_paise(). "
        f"Use Decimal, int, or str."
    )


def _round_to_paise(decimal_value: Decimal) -> int:
    """
    Round Decimal rupee value to integer paise using ROUND_HALF_UP.
    
    Internal helper — always use to_paise() in calling code.
    """
    # Multiply by 100, round to 0 decimal places (paise scale)
    paise_decimal = (decimal_value * PAISE_PER_RUPEE).quantize(
        Decimal('1'), rounding=ROUNDING_POLICY
    )
    return int(paise_decimal)


def from_paise(paise: int) -> Decimal:
    """
    Convert integer paise back to Decimal rupees.
    
    DISPLAY ONLY — do not use for calculations.
    
    Args:
        paise: Integer paise amount
    
    Returns:
        Decimal rupee value with 2 decimal places
    
    Examples:
        >>> from_paise(10050)
        Decimal('100.50')
        >>> from_paise(123456)
        Decimal('1234.56')
    """
    return (Decimal(paise) / PAISE_PER_RUPEE).quantize(_FINANCIAL_CTX)


# ============================================================
# Arithmetic Operations
# ============================================================

def add_paise(a: int, b: int) -> int:
    """Add two paise amounts. Returns int paise."""
    return a + b


def subtract_paise(a: int, b: int) -> int:
    """Subtract b from a. Returns int paise."""
    return a - b


def multiply_paise(paise: int, factor: Decimal) -> int:
    """
    Multiply paise by a Decimal factor.
    
    Uses Decimal arithmetic, rounds to nearest paise.
    
    Args:
        paise: Integer paise amount
        factor: Decimal multiplier (e.g., Decimal('1.15') for 15% interest)
    
    Returns:
        Integer paise result, rounded ROUND_HALF_UP
    """
    result = Decimal(paise) * factor
    return _round_to_paise(result)


def divide_paise(paise: int, divisor: Decimal) -> int:
    """
    Divide paise by a Decimal divisor.
    
    Uses Decimal arithmetic, rounds to nearest paise.
    
    Args:
        paise: Integer paise amount
        divisor: Decimal divisor (must not be zero)
    
    Returns:
        Integer paise result, rounded ROUND_HALF_UP
    """
    if divisor == 0:
        raise ZeroDivisionError("Cannot divide paise by zero")
    result = Decimal(paise) / divisor
    return _round_to_paise(result)


def percentage_of(paise: int, percent: Decimal) -> int:
    """
    Calculate percentage of paise amount.
    
    Args:
        paise: Integer paise amount
        percent: Decimal percentage (e.g., Decimal('15.0') for 15%)
    
    Returns:
        Integer paise result
    """
    return multiply_paise(paise, percent / Decimal('100'))


# ============================================================
# Validation
# ============================================================

def validate_paise(value: int, name: str = "value") -> None:
    """
    Validate that a value is a valid paise amount.
    
    Args:
        value: Integer to validate
        name: Field name for error messages
    
    Raises:
        TypeError: If value is not int
        ValueError: If value is None
    """
    if not isinstance(value, int):
        raise TypeError(f"{name} must be int (paise), got {type(value)}")
    if value is None:
        raise ValueError(f"{name} cannot be None")


def validate_non_negative_paise(value: int, name: str = "value") -> None:
    """
    Validate that a paise amount is non-negative.
    
    Args:
        value: Integer paise amount
        name: Field name for error messages
    
    Raises:
        TypeError: If value is not int
        ValueError: If value is None or negative
    """
    validate_paise(value, name)
    if value < 0:
        raise ValueError(f"{name} cannot be negative: {value}")


def validate_positive_paise(value: int, name: str = "value") -> None:
    """
    Validate that a paise amount is strictly positive.
    
    Args:
        value: Integer paise amount
        name: Field name for error messages
    
    Raises:
        TypeError: If value is not int
        ValueError: If value is None or zero or negative
    """
    validate_paise(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be positive: {value}")


# ============================================================
# Display Helpers
# ============================================================

def format_paise_display(paise: int) -> str:
    """
    Format paise for human-readable display.
    
    Args:
        paise: Integer paise amount
    
    Returns:
        Formatted string like "₹1,234.56" or "-₹1,234.56"
    """
    rupees = from_paise(paise)
    sign = '-' if rupees < 0 else ''
    abs_rupees = abs(rupees)
    return f"{sign}₹{abs_rupees:,.2f}"


# ============================================================
# Export Public API
# ============================================================

__all__ = [
    'to_paise',
    'from_paise',
    'add_paise',
    'subtract_paise',
    'multiply_paise',
    'divide_paise',
    'percentage_of',
    'validate_paise',
    'validate_non_negative_paise',
    'validate_positive_paise',
    'format_paise_display',
    'PAISE_PER_RUPEE',
    'ROUNDING_POLICY',
    'PAISE_SCALE',
]