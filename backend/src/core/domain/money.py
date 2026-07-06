"""
Money Domain Model
==================

Canonical monetary value representation using integer paise.

Design Principles:
- Immutable: All operations return new Money instances
- Type-safe: Only accepts integer paise, rejects floats
- Arithmetic: Safe add/subtract/multiply/divide operations
- No serialization: Serialization handled by mapper/DTO layer
- No business limits: Business rules belong in higher layers

Architecture Rule: All monetary values in the system MUST be represented
as integer paise internally. No floating-point arithmetic for money.
"""

from typing import Union


class Money:
    """
    Immutable monetary value represented in paise (integer).
    
    1 INR = 100 paise
    Example: ₹1,234.56 = 123456 paise
    
    This class enforces the canonical monetary representation for the entire
    backend system. All financial calculations must use this class.
    
    Note: Serialization (to_dict, from_dict) is handled by the mapper/DTO layer.
    Business limits (e.g., max amount) are enforced in higher layers.
    """
    
    __slots__ = ('_paise',)
    
    def __init__(self, paise: int):
        """
        Create a Money instance from paise.
        
        Args:
            paise: Amount in paise (must be integer)
            
        Raises:
            TypeError: If paise is not an integer
        """
        if not isinstance(paise, int):
            raise TypeError(
                f"Money must be created with integer paise, got {type(paise).__name__}: {paise}"
            )
        
        self._paise = paise
    
    @property
    def paise(self) -> int:
        """Get the amount in paise (integer)."""
        return self._paise
    
    def to_rupees(self) -> float:
        """
        Convert to rupees (float).
        
        Warning: Use this only for display/formatting purposes.
        All calculations should remain in paise to avoid floating-point drift.
        """
        return self._paise / 100.0
    
    @classmethod
    def from_rupees(cls, rupees: Union[int, float]) -> 'Money':
        """
        Create Money from rupees (float or int).
        
        Uses rounding to handle floating-point precision issues.
        
        Args:
            rupees: Amount in rupees
            
        Returns:
            Money instance in paise
        """
        paise = round(rupees * 100)
        return cls(paise)
    
    # ============================================================
    # Arithmetic Operations (all return new Money instances)
    # ============================================================
    
    def add(self, other: 'Money') -> 'Money':
        """
        Add two Money values.
        
        Args:
            other: Money instance to add
            
        Returns:
            New Money instance with sum
        """
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money and {type(other).__name__}")
        return Money(self._paise + other._paise)
    
    def subtract(self, other: 'Money') -> 'Money':
        """
        Subtract two Money values.
        
        Args:
            other: Money instance to subtract
            
        Returns:
            New Money instance with difference
        """
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract {type(other).__name__} from Money")
        return Money(self._paise - other._paise)
    
    def multiply(self, factor: int) -> 'Money':
        """
        Multiply by integer factor.
        
        Args:
            factor: Integer multiplier
            
        Returns:
            New Money instance with product
        """
        if not isinstance(factor, int):
            raise TypeError(f"Money can only be multiplied by int, got {type(factor).__name__}")
        return Money(self._paise * factor)
    
    def divide(self, divisor: int) -> 'Money':
        """
        Divide by integer divisor (integer division).
        
        Args:
            divisor: Integer divisor
            
        Returns:
            New Money instance with quotient (rounded)
            
        Raises:
            ZeroDivisionError: If divisor is 0
        """
        if not isinstance(divisor, int):
            raise TypeError(f"Money can only be divided by int, got {type(divisor).__name__}")
        if divisor == 0:
            raise ZeroDivisionError("Cannot divide Money by zero")
        return Money(round(self._paise / divisor))
    
    def percentage(self, percent: int) -> 'Money':
        """
        Calculate percentage of this amount.
        
        Args:
            percent: Percentage (0-100)
            
        Returns:
            New Money instance with percentage amount
        """
        if not isinstance(percent, int):
            raise TypeError(f"Percentage must be int, got {type(percent).__name__}")
        if not (0 <= percent <= 100):
            raise ValueError(f"Percentage must be 0-100, got {percent}")
        return Money(round(self._paise * percent / 100))
    
    def negate(self) -> 'Money':
        """
        Negate the amount (positive → negative, negative → positive).
        
        Returns:
            New Money instance with negated value
        """
        return Money(-self._paise)
    
    def absolute(self) -> 'Money':
        """
        Get absolute value.
        
        Returns:
            New Money instance with absolute value
        """
        return Money(abs(self._paise))
    
    # ============================================================
    # Comparison Operations
    # ============================================================
    
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self._paise == 0
    
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self._paise > 0
    
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self._paise < 0
    
    def equals(self, other: 'Money') -> bool:
        """
        Check equality with another Money instance.
        
        Args:
            other: Money instance to compare
            
        Returns:
            True if amounts are equal
        """
        if not isinstance(other, Money):
            return False
        return self._paise == other._paise
    
    def compare(self, other: 'Money') -> int:
        """
        Compare with another Money instance.
        
        Args:
            other: Money instance to compare
            
        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money with {type(other).__name__}")
        if self._paise < other._paise:
            return -1
        elif self._paise > other._paise:
            return 1
        return 0
    
    # ============================================================
    # String Representation
    # ============================================================
    
    def __str__(self) -> str:
        """String representation showing both paise and rupees."""
        rupees = self._paise / 100.0
        return f"₹{rupees:,.2f} ({self._paise} paise)"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"Money(paise={self._paise})"
    
    def __format__(self, format_spec: str) -> str:
        """Format support for f-strings."""
        if format_spec == 'rupees':
            return f"₹{self._paise / 100.0:,.2f}"
        elif format_spec == 'paise':
            return f"{self._paise} paise"
        return str(self)
    
    # ============================================================
    # Python Magic Methods (for convenience)
    # ============================================================
    
    def __add__(self, other: 'Money') -> 'Money':
        """Support + operator."""
        return self.add(other)
    
    def __sub__(self, other: 'Money') -> 'Money':
        """Support - operator."""
        return self.subtract(other)
    
    def __mul__(self, factor: int) -> 'Money':
        """Support * operator."""
        return self.multiply(factor)
    
    def __rmul__(self, factor: int) -> 'Money':
        """Support reflected * operator."""
        return self.multiply(factor)
    
    def __truediv__(self, divisor: int) -> 'Money':
        """Support / operator."""
        return self.divide(divisor)
    
    def __neg__(self) -> 'Money':
        """Support unary - operator."""
        return self.negate()
    
    def __abs__(self) -> 'Money':
        """Support abs() function."""
        return self.absolute()
    
    def __eq__(self, other: object) -> bool:
        """Support == operator."""
        if not isinstance(other, Money):
            return NotImplemented
        return self._paise == other._paise
    
    def __lt__(self, other: 'Money') -> bool:
        """Support < operator."""
        if not isinstance(other, Money):
            return NotImplemented
        return self._paise < other._paise
    
    def __le__(self, other: 'Money') -> bool:
        """Support <= operator."""
        if not isinstance(other, Money):
            return NotImplemented
        return self._paise <= other._paise
    
    def __gt__(self, other: 'Money') -> bool:
        """Support > operator."""
        if not isinstance(other, Money):
            return NotImplemented
        return self._paise > other._paise
    
    def __ge__(self, other: 'Money') -> bool:
        """Support >= operator."""
        if not isinstance(other, Money):
            return NotImplemented
        return self._paise >= other._paise
    
    def __hash__(self) -> int:
        """Support use in sets and as dict keys."""
        return hash(self._paise)