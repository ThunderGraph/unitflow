"""Keyword-first unit definition helpers."""

from __future__ import annotations

from fractions import Fraction

from unitflow.core.quantities import Quantity
from unitflow.core.scale import Scale
from unitflow.core.units import Unit
from unitflow.core.unit_families import UnitFamily
from unitflow.errors import UnitError


def _scale_from_exact_magnitude(value: int | Fraction) -> Scale:
    return Scale(Fraction(value, 1) if isinstance(value, int) else value)


def define_unit(
    *,
    name: str,
    symbol: str,
    expr: Unit | Quantity,
    aliases: tuple[str, ...] = (),
    family: UnitFamily | None = None,
    quantity_kind: str | None = None,
) -> Unit:
    """Define a new semantic unit from an existing unit or exact quantity expression."""

    if not isinstance(name, str) or not name.strip():
        raise UnitError("define_unit() requires a non-empty unit name.")
    if not isinstance(symbol, str) or not symbol.strip():
        raise UnitError("define_unit() requires a non-empty unit symbol.")
    if not isinstance(aliases, tuple):
        raise UnitError("define_unit() aliases must be a tuple of strings.")
    for alias in aliases:
        if not isinstance(alias, str) or not alias.strip():
            raise UnitError("define_unit() aliases must contain only non-empty strings.")

    if isinstance(expr, Unit):
        dimension = expr.dimension
        scale = expr.scale
        inherited_family = expr.family
    elif isinstance(expr, Quantity):
        if isinstance(expr.magnitude, float):
            raise UnitError(
                "define_unit() only supports exact quantity magnitudes. Use int or Fraction, not float."
            )
        dimension = expr.unit.dimension
        scale = _scale_from_exact_magnitude(expr.magnitude) * expr.unit.scale
        inherited_family = expr.unit.family
    else:
        raise UnitError("define_unit() expr must be a Unit or an exact Quantity.")

    return Unit(
        dimension=dimension,
        scale=scale,
        name=name,
        symbol=symbol,
        aliases=aliases,
        family=inherited_family if family is None else family,
        quantity_kind=expr.quantity_kind if quantity_kind is None and isinstance(expr, Unit) else quantity_kind,
    )
