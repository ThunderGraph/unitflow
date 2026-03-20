"""Concrete quantity semantics for unitflow."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import TYPE_CHECKING, Any, TypeAlias, Union

from unitflow.core.scale import Scale
from unitflow.core.units import Unit
from unitflow.errors import DimensionMismatchError, QuantityError

if TYPE_CHECKING:
    import numpy as np
    ScalarMagnitude: TypeAlias = Union[int, float, Fraction, "np.ndarray[Any, Any]"]
else:
    ScalarMagnitude: TypeAlias = Any


_is_numpy_array_func = None

def _is_numpy_array(value: Any) -> bool:
    global _is_numpy_array_func
    if _is_numpy_array_func is None:
        try:
            from unitflow.backends.numpy import is_numpy_array as f
            _is_numpy_array_func = f
        except ImportError:
            _is_numpy_array_func = lambda v: False
    return _is_numpy_array_func(value)

def is_supported_magnitude(value: object) -> bool:
    """Whether the quantity core supports this magnitude type."""

    if isinstance(value, (int, float, Fraction)) and not isinstance(value, bool):
        return True

    return _is_numpy_array(value)

def _require_supported_magnitude(value: object, *, context: str) -> ScalarMagnitude:
    if not is_supported_magnitude(value):
        raise QuantityError(
            f"{context} only supports int, float, Fraction, or compatible array magnitudes."
        )
    return value

def _apply_scale_to_magnitude(magnitude: ScalarMagnitude, scale: Scale) -> ScalarMagnitude:
    """Apply a scale factor to a concrete magnitude."""

    if _is_numpy_array(magnitude):
        if scale.pi_power == 0:
            return magnitude * float(scale.coefficient)
        return magnitude * scale.as_float()

    if scale.pi_power == 0:
        return magnitude * scale.coefficient
    return float(magnitude) * scale.as_float()

def _divide_magnitudes(left: ScalarMagnitude, right: ScalarMagnitude) -> ScalarMagnitude:
    """Divide magnitudes while preserving exactness where possible."""

    if _is_numpy_array(left) or _is_numpy_array(right):
        return left / right

    if isinstance(left, float) or isinstance(right, float):
        return left / right
    return Fraction(left) / Fraction(right)


@dataclass(frozen=True, slots=True, eq=False)
class Quantity:
    """Concrete magnitude plus semantic unit."""

    magnitude: ScalarMagnitude
    unit: Unit
    _explicit_display: bool = False

    def __post_init__(self) -> None:
        magnitude = _require_supported_magnitude(self.magnitude, context="Quantity")
        if not isinstance(self.unit, Unit):
            raise QuantityError("Quantity.unit must be a Unit.")
        object.__setattr__(self, "magnitude", magnitude)

    def to(self, target_unit: Unit) -> Quantity:
        if not isinstance(target_unit, Unit):
            raise QuantityError("Quantity.to() expects a Unit target.")
        factor = self.unit.conversion_factor_to(target_unit)
        return Quantity(_apply_scale_to_magnitude(self.magnitude, factor), target_unit, _explicit_display=True)

    def is_close(
        self,
        other: object,
        *,
        rel_tol: float = 1e-9,
        abs_tol: float = 0.0,
    ) -> bool:
        if not isinstance(other, Quantity):
            return False
        if not self.unit.is_compatible_with(other.unit):
            return False
        other_converted = other.to(self.unit)
        return math.isclose(float(self.magnitude), float(other_converted.magnitude), rel_tol=rel_tol, abs_tol=abs_tol)

    def _semantic_exact_value(self) -> Fraction | None:
        if self.unit.scale.pi_power != 0:
            return None
        if isinstance(self.magnitude, float):
            return None
        return Fraction(self.magnitude) * self.unit.scale.coefficient

    def _semantic_float_key(self) -> tuple[object, float]:
        normalized = _apply_scale_to_magnitude(self.magnitude, self.unit.scale)
        return self.unit.dimension, float(normalized)

    def __neg__(self) -> Quantity:
        return Quantity(-self.magnitude, self.unit)

    def __add__(self, other: object) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        if not self.unit.is_compatible_with(other.unit):
            raise DimensionMismatchError(
                f"Cannot add quantities with dimensions {self.unit.dimension!r} and {other.unit.dimension!r}."
            )
        other_converted = other.to(self.unit)
        return Quantity(self.magnitude + other_converted.magnitude, self.unit)

    def __sub__(self, other: object) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        if not self.unit.is_compatible_with(other.unit):
            raise DimensionMismatchError(
                f"Cannot subtract quantities with dimensions {self.unit.dimension!r} and {other.unit.dimension!r}."
            )
        other_converted = other.to(self.unit)
        return Quantity(self.magnitude - other_converted.magnitude, self.unit)

    def __mul__(self, other: object) -> Quantity:
        if isinstance(other, Quantity):
            return Quantity(self.magnitude * other.magnitude, self.unit * other.unit)
        if isinstance(other, Unit):
            return Quantity(self.magnitude, self.unit * other)
        if is_supported_magnitude(other):
            return Quantity(self.magnitude * other, self.unit)
        return NotImplemented

    def __rmul__(self, other: object) -> Quantity:
        if is_supported_magnitude(other):
            return Quantity(other * self.magnitude, self.unit, _explicit_display=self._explicit_display)
        return NotImplemented

    def __truediv__(self, other: object) -> Quantity:
        if isinstance(other, Quantity):
            return Quantity(_divide_magnitudes(self.magnitude, other.magnitude), self.unit / other.unit)
        if isinstance(other, Unit):
            return Quantity(self.magnitude, self.unit / other)
        if is_supported_magnitude(other):
            return Quantity(_divide_magnitudes(self.magnitude, other), self.unit)
        return NotImplemented

    def __rtruediv__(self, other: object) -> Quantity:
        if is_supported_magnitude(other):
            return Quantity(_divide_magnitudes(other, self.magnitude), Unit.dimensionless() / self.unit)
        return NotImplemented

    def __pow__(self, power: object) -> Quantity:
        if not isinstance(power, int):
            raise QuantityError("Quantities can only be raised to integer powers.")
        return Quantity(self.magnitude**power, self.unit**power)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        if not self.unit.is_compatible_with(other.unit):
            return False

        left_exact = self._semantic_exact_value()
        right_exact = other._semantic_exact_value()
        if left_exact is not None and right_exact is not None:
            return left_exact == right_exact
        return self._semantic_float_key() == other._semantic_float_key()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        if not self.unit.is_compatible_with(other.unit):
            raise DimensionMismatchError(
                f"Cannot compare quantities with dimensions {self.unit.dimension!r} and {other.unit.dimension!r}."
            )
        other_converted = other.to(self.unit)
        return float(self.magnitude) < float(other_converted.magnitude)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        if not self.unit.is_compatible_with(other.unit):
            raise DimensionMismatchError(
                f"Cannot compare quantities with dimensions {self.unit.dimension!r} and {other.unit.dimension!r}."
            )
        other_converted = other.to(self.unit)
        return float(self.magnitude) <= float(other_converted.magnitude)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        if not self.unit.is_compatible_with(other.unit):
            raise DimensionMismatchError(
                f"Cannot compare quantities with dimensions {self.unit.dimension!r} and {other.unit.dimension!r}."
            )
        other_converted = other.to(self.unit)
        return float(self.magnitude) > float(other_converted.magnitude)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        if not self.unit.is_compatible_with(other.unit):
            raise DimensionMismatchError(
                f"Cannot compare quantities with dimensions {self.unit.dimension!r} and {other.unit.dimension!r}."
            )
        other_converted = other.to(self.unit)
        return float(self.magnitude) >= float(other_converted.magnitude)

    def __array_ufunc__(self, ufunc: Any, method: str, *inputs: Any, **kwargs: Any) -> Any:
        try:
            from unitflow.backends.numpy import _handle_numpy_ufunc
            return _handle_numpy_ufunc(self, ufunc, method, *inputs, **kwargs)
        except ImportError:
            return NotImplemented

    def __array_function__(self, func: Any, types: Any, args: Any, kwargs: Any) -> Any:
        try:
            from unitflow.backends.numpy import _handle_numpy_function
            return _handle_numpy_function(self, func, types, args, kwargs)
        except ImportError:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self._semantic_float_key())

    def __repr__(self) -> str:
        return f"Quantity(magnitude={self.magnitude!r}, unit={self.unit!r})"

    def __str__(self) -> str:
        from unitflow.core.display import default_resolver

        if self._explicit_display:
            resolved = self
        else:
            resolved = default_resolver.resolve(self)
        unit_str = default_resolver.resolve_unit_symbol(resolved.unit)

        mag = resolved.magnitude
        if isinstance(mag, Fraction) and mag.denominator != 1:
            mag = float(mag)

        if unit_str:
            return f"{mag} {unit_str}"
        return str(mag)
