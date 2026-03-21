"""NumPy backend integration layer for unitflow."""
# mypy: disable-error-code="arg-type"

from __future__ import annotations

import sys
from typing import Any

from unitflow.core.quantities import Quantity
from unitflow.errors import DimensionMismatchError


def is_numpy_array(value: Any) -> bool:
    """Check if a value is a numpy array without requiring a hard import."""
    if "numpy" not in sys.modules:
        return False
    import numpy as np

    return isinstance(value, np.ndarray)


def _handle_numpy_ufunc(
    quantity: Quantity, ufunc: Any, method: str, *inputs: Any, **kwargs: Any
) -> Any:
    """Implement NumPy's __array_ufunc__ dispatch protocol for Quantity."""
    import numpy as np

    if method not in ("__call__", "reduce"):
        return NotImplemented

    # Unpack `out` arguments if present
    out = kwargs.get("out", tuple())
    custom_out = False
    if out:
        out_mags = tuple(o.magnitude if isinstance(o, Quantity) else o for o in out)
        kwargs["out"] = out_mags
        custom_out = True

    if method == "reduce":
        # Handle reductions like np.sum (np.add.reduce)
        if ufunc in (np.add,):
            return _ufunc_reduce_add(ufunc, *inputs, **kwargs)
        return NotImplemented

    # Multiplication and Division
    if ufunc in (np.multiply, np.divide, np.true_divide):
        return _ufunc_mul_div(ufunc, custom_out, out, *inputs, **kwargs)

    # Addition and Subtraction
    if ufunc in (np.add, np.subtract):
        return _ufunc_add_sub(ufunc, custom_out, out, *inputs, **kwargs)

    # Powers
    if ufunc in (np.power, np.square, np.sqrt):
        return _ufunc_power(ufunc, custom_out, out, *inputs, **kwargs)

    # Dimensionless transcendentals
    if ufunc in (np.sin, np.cos, np.tan, np.exp, np.log, np.log10, np.log2):
        return _ufunc_dimensionless(ufunc, custom_out, out, *inputs, **kwargs)

    return NotImplemented

def _format_result(result_mag: Any, unit: Any, custom_out: bool, orig_out: Any) -> Any:
    if custom_out:
        return orig_out[0]
    return Quantity(result_mag, unit)

def _ufunc_reduce_add(ufunc: Any, *inputs: Any, **kwargs: Any) -> Any:
    q = inputs[0]
    if not isinstance(q, Quantity):
        return NotImplemented

    # Unwrap any other Quantity arguments (like `initial` passed positionally)
    new_inputs = tuple(
        (i.to(q.unit).magnitude if isinstance(i, Quantity) else i)
        for i in inputs[1:]
    )

    # Unwrap any Quantity arguments in kwargs (like `initial` or `where`)
    new_kwargs = {}
    for k, v in kwargs.items():
        if isinstance(v, Quantity):
            new_kwargs[k] = v.to(q.unit).magnitude
        else:
            new_kwargs[k] = v

    result_mag = ufunc.reduce(q.magnitude, *new_inputs, **new_kwargs)
    return Quantity(result_mag, q.unit)

def _ufunc_mul_div(ufunc: Any, custom_out: bool, orig_out: Any, *inputs: Any, **kwargs: Any) -> Any:
    """Handle ufuncs that multiply or divide units."""
    import numpy as np

    left, right = inputs[0], inputs[1]

    left_mag = left.magnitude if isinstance(left, Quantity) else left
    right_mag = right.magnitude if isinstance(right, Quantity) else right
    result_mag = ufunc(left_mag, right_mag, **kwargs)

    if isinstance(left, Quantity) and isinstance(right, Quantity):
        if ufunc is np.multiply:
            return _format_result(result_mag, left.unit * right.unit, custom_out, orig_out)
        else:
            return _format_result(result_mag, left.unit / right.unit, custom_out, orig_out)

    if isinstance(left, Quantity):
        return _format_result(result_mag, left.unit, custom_out, orig_out)

    if isinstance(right, Quantity):
        if ufunc is np.multiply:
            return _format_result(result_mag, right.unit, custom_out, orig_out)
        else:
            from unitflow.core.units import Unit
            return _format_result(result_mag, Unit.dimensionless() / right.unit, custom_out, orig_out)

    return NotImplemented


def _ufunc_add_sub(ufunc: Any, custom_out: bool, orig_out: Any, *inputs: Any, **kwargs: Any) -> Any:
    """Handle ufuncs that require compatible units."""
    left, right = inputs[0], inputs[1]

    if not isinstance(left, Quantity) or not isinstance(right, Quantity):
        # We don't support adding raw arrays to quantities, just like scalar core
        raise DimensionMismatchError("Cannot add or subtract a dimensionless scalar/array and a unit-bearing quantity.")

    if not left.unit.is_compatible_with(right.unit):
        raise DimensionMismatchError(
            f"Cannot add/subtract arrays with dimensions {left.unit.dimension!r} and {right.unit.dimension!r}."
        )

    right_converted = right.to(left.unit)
    result_mag = ufunc(left.magnitude, right_converted.magnitude, **kwargs)
    return _format_result(result_mag, left.unit, custom_out, orig_out)


def _ufunc_power(ufunc: Any, custom_out: bool, orig_out: Any, *inputs: Any, **kwargs: Any) -> Any:
    """Handle powers, squares, and square roots."""
    import numpy as np

    if ufunc is np.sqrt:
        return NotImplemented

    if ufunc is np.square:
        q = inputs[0]
        if not isinstance(q, Quantity):
            return NotImplemented
        return _format_result(np.square(q.magnitude, **kwargs), q.unit ** 2, custom_out, orig_out)

    if ufunc is np.power:
        base, power = inputs[0], inputs[1]
        if not isinstance(base, Quantity):
            return NotImplemented

        if np.isscalar(power):
            power_val = int(power)
            if power_val == power:
                return _format_result(np.power(base.magnitude, power, **kwargs), base.unit ** power_val, custom_out, orig_out)

        return NotImplemented


def _ufunc_dimensionless(ufunc: Any, custom_out: bool, orig_out: Any, *inputs: Any, **kwargs: Any) -> Any:
    """Handle transcendentals which require dimensionless inputs."""
    q = inputs[0]
    if not isinstance(q, Quantity):
        return NotImplemented

    if not q.unit.dimension.is_dimensionless:
        raise DimensionMismatchError(
            f"Transcendental function {ufunc.__name__} requires a dimensionless input, got {q.unit.dimension!r}."
        )

    normalized_mag = q.magnitude
    if q.unit.scale.pi_power != 0 or q.unit.scale.coefficient != 1:
        normalized_mag = q.magnitude * q.unit.scale.as_float()

    from unitflow.core.units import Unit
    return _format_result(ufunc(normalized_mag, **kwargs), Unit.dimensionless(), custom_out, orig_out)


def _handle_numpy_function(
    quantity: Quantity, func: Any, types: Any, args: Any, kwargs: Any
) -> Any:
    """Implement NumPy's __array_function__ dispatch protocol for Quantity."""
    import numpy as np

    if func in (np.sum, np.mean, np.median, np.min, np.max):
        first_unit = None

        # Check all quantity arguments for unit compatibility
        for arg in args:
            if isinstance(arg, Quantity):
                if first_unit is None:
                    first_unit = arg.unit
                elif not arg.unit.is_compatible_with(first_unit):
                    raise DimensionMismatchError(
                        f"Cannot perform {func.__name__} across quantities with incompatible units."
                    )

        if first_unit is None:
            return NotImplemented

        # Normalize any differing units to the first unit
        new_args = tuple(
            a.to(first_unit).magnitude if isinstance(a, Quantity) else a for a in args
        )
        new_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, Quantity):
                if not v.unit.is_compatible_with(first_unit):
                    raise DimensionMismatchError(
                        f"Cannot perform {func.__name__} with incompatible kwargs unit."
                    )
                new_kwargs[k] = v.to(first_unit).magnitude
            else:
                new_kwargs[k] = v
        res_mag = func(*new_args, **new_kwargs)
        return Quantity(res_mag, first_unit)

    return NotImplemented
