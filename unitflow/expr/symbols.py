"""Symbol node and constructor for the expression layer."""

from __future__ import annotations

from dataclasses import dataclass

from unitflow.core.dimensions import Dimension
from unitflow.core.quantities import Quantity
from unitflow.core.units import Unit
from unitflow.expr.errors import EvaluationError, ExprError
from unitflow.expr.expressions import Expr


@dataclass(frozen=True, slots=True, eq=False)
class Symbol(Expr):
    """A symbolic variable with dimension and optional unit bindings."""

    name: str
    _dimension: Dimension
    unit: Unit | None = None
    quantity_kind: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ExprError("Symbol name must be a non-empty string.")
        if not isinstance(self._dimension, Dimension):
            raise ExprError("Symbol dimension must be a Dimension instance.")
        if self.unit is not None:
            if not isinstance(self.unit, Unit):
                raise ExprError("Symbol unit must be a Unit instance.")
            if self.unit.dimension != self._dimension:
                raise ExprError("Symbol unit dimension must match symbol dimension.")

    @property
    def dimension(self) -> Dimension:
        return self._dimension

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        return frozenset({self})

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        """Look up this symbol's value in the context.

        Context keys must be the **same Symbol instances** used to build the
        expression (identity-based lookup). Constructing a new Symbol with the
        same name/unit and using it as a key will fail because Expr.__eq__
        returns an Equation, not a bool.
        """
        for key in context:
            if key is self:
                return context[key]
        raise EvaluationError(f"Symbol '{self.name}' is not bound in the evaluation context.")

    def is_same(self, other: object) -> bool:
        if not isinstance(other, Symbol):
            return False
        return (
            self.name == other.name
            and self._dimension == other._dimension
            and self.unit == other.unit
            and self.quantity_kind == other.quantity_kind
        )

    def __hash__(self) -> int:
        return hash((self.name, self._dimension, self.unit, self.quantity_kind))


def symbol(
    name: str,
    *,
    dimension: Dimension | None = None,
    unit: Unit | None = None,
    quantity_kind: str | None = None,
) -> Symbol:
    """Create a new symbol with either a unit or dimension."""

    if dimension is None and unit is None:
        raise ExprError("symbol() requires at least a dimension or a unit.")

    resolved_dimension = dimension
    if unit is not None:
        if dimension is not None and dimension != unit.dimension:
            raise ExprError("symbol() dimension and unit dimension must agree.")
        resolved_dimension = unit.dimension

    return Symbol(
        name=name,
        _dimension=resolved_dimension,  # type: ignore[arg-type]
        unit=unit,
        quantity_kind=quantity_kind,
    )
