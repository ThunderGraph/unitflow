"""Exact scale semantics for unitflow."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

from unitflow.errors import ScaleError


@dataclass(frozen=True, slots=True)
class Scale:
    """Exact scale represented as a rational coefficient times an integer power of pi."""

    coefficient: Fraction
    pi_power: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.coefficient, float):
            raise ScaleError(
                "Scale coefficients must not be floats. Use Fraction or Scale.from_ratio() for exact semantics."
            )
        coefficient = Fraction(self.coefficient)
        if coefficient == 0 and self.pi_power != 0:
            raise ScaleError("Zero scale cannot carry a non-zero power of pi.")
        if not isinstance(self.pi_power, int):
            raise ScaleError("Scale pi_power must be an integer.")
        object.__setattr__(self, "coefficient", coefficient)

    @classmethod
    def one(cls) -> Scale:
        return cls(Fraction(1, 1), 0)

    @classmethod
    def zero(cls) -> Scale:
        return cls(Fraction(0, 1), 0)

    @classmethod
    def from_int(cls, value: int) -> Scale:
        if not isinstance(value, int):
            raise ScaleError("Scale.from_int expects an integer.")
        return cls(Fraction(value, 1), 0)

    @classmethod
    def from_ratio(cls, numerator: int, denominator: int = 1, *, pi_power: int = 0) -> Scale:
        if not isinstance(numerator, int) or not isinstance(denominator, int):
            raise ScaleError("Scale ratios must use integer numerators and denominators.")
        if denominator == 0:
            raise ScaleError("Scale denominator cannot be zero.")
        return cls(Fraction(numerator, denominator), pi_power)

    @classmethod
    def pi(cls) -> Scale:
        return cls(Fraction(1, 1), 1)

    @property
    def is_zero(self) -> bool:
        return self.coefficient == 0

    def __mul__(self, other: Scale) -> Scale:
        if not isinstance(other, Scale):
            return NotImplemented
        return Scale(self.coefficient * other.coefficient, self.pi_power + other.pi_power)

    def __truediv__(self, other: Scale) -> Scale:
        if not isinstance(other, Scale):
            return NotImplemented
        if other.is_zero:
            raise ScaleError("Cannot divide by a zero scale.")
        return Scale(self.coefficient / other.coefficient, self.pi_power - other.pi_power)

    def __pow__(self, power: int) -> Scale:
        if not isinstance(power, int):
            raise ScaleError("Scales can only be raised to integer powers in the semantic core.")
        if power < 0 and self.is_zero:
            raise ScaleError("Zero scale cannot be raised to a negative power.")
        return Scale(self.coefficient**power, self.pi_power * power)

    def as_float(self) -> float:
        """Lossy float conversion for debugging and later backend integration."""

        return float(self.coefficient) * (math.pi**self.pi_power)

    def __repr__(self) -> str:
        if self.is_zero:
            return "Scale(0)"
        if self.pi_power == 0:
            return f"Scale({self.coefficient})"
        if self.coefficient == 1:
            return f"Scale(pi^{self.pi_power})"
        return f"Scale({self.coefficient} * pi^{self.pi_power})"
