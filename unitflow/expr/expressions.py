"""Symbolic AST nodes and base expression class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from unitflow.core.dimensions import Dimension
from unitflow.core.quantities import Quantity, is_supported_magnitude
from unitflow.core.units import Unit
from unitflow.expr.errors import DimensionMismatchExprError, ExprError

if TYPE_CHECKING:
    from unitflow.expr.constraints import Constraint
    from unitflow.expr.symbols import Symbol


class Expr:
    """Base class for all symbolic expressions."""

    @property
    def dimension(self) -> Dimension:
        raise NotImplementedError

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        raise NotImplementedError

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        """Evaluate this expression against a context of realized scalar values.

        Context keys must be the same Symbol instances used to build the
        expression. Array-backed quantities are not supported in v0.
        """
        raise NotImplementedError

    def to(self, target_unit: Unit) -> Expr:
        if not isinstance(target_unit, Unit):
            raise ExprError("target_unit must be a Unit.")
        if self.dimension != target_unit.dimension:
            raise DimensionMismatchExprError(
                f"Cannot convert expression with dimension {self.dimension!r} to unit with dimension {target_unit.dimension!r}."
            )
        return ConversionExpr(self, target_unit)

    def is_same(self, other: Any) -> bool:
        """Check if this expression is structurally identical to another."""
        if type(self) is not type(other):
            return False
        if hasattr(self, "__dataclass_fields__"):
            for field in self.__dataclass_fields__:
                val1 = getattr(self, field)
                val2 = getattr(other, field)
                if isinstance(val1, Expr) and isinstance(val2, Expr):
                    if not val1.is_same(val2):
                        return False
                else:
                    if val1 != val2:
                        return False
            return True
        return self is other

    def __add__(self, other: Any) -> Expr:
        return _dispatch_add(self, other)

    def __radd__(self, other: Any) -> Expr:
        return _dispatch_add(other, self)

    def __sub__(self, other: Any) -> Expr:
        return _dispatch_sub(self, other)

    def __rsub__(self, other: Any) -> Expr:
        return _dispatch_sub(other, self)

    def __mul__(self, other: Any) -> Expr:
        return _dispatch_mul(self, other)

    def __rmul__(self, other: Any) -> Expr:
        return _dispatch_mul(other, self)

    def __truediv__(self, other: Any) -> Expr:
        return _dispatch_div(self, other)

    def __rtruediv__(self, other: Any) -> Expr:
        return _dispatch_div(other, self)

    def __pow__(self, power: int) -> Expr:
        return _dispatch_pow(self, power)

    def __eq__(self, other: Any) -> Constraint:  # type: ignore[override]
        from unitflow.expr.constraints import Equation

        return Equation(self, _promote(other))

    def __lt__(self, other: Any) -> Constraint:
        from unitflow.expr.constraints import StrictInequality

        return StrictInequality(self, _promote(other), "<")

    def __le__(self, other: Any) -> Constraint:
        from unitflow.expr.constraints import NonStrictInequality

        return NonStrictInequality(self, _promote(other), "<=")

    def __gt__(self, other: Any) -> Constraint:
        from unitflow.expr.constraints import StrictInequality

        return StrictInequality(self, _promote(other), ">")

    def __ge__(self, other: Any) -> Constraint:
        from unitflow.expr.constraints import NonStrictInequality

        return NonStrictInequality(self, _promote(other), ">=")

    def __hash__(self) -> int:
        return id(self)


def _promote(value: Any) -> Expr:
    if isinstance(value, Expr):
        return value
    if isinstance(value, Quantity):
        return QuantityExpr(value)
    if is_supported_magnitude(value):
        return QuantityExpr(Quantity(value, Unit.dimensionless()))
    raise ExprError(f"Cannot promote {type(value).__name__} to Expr.")


def _dispatch_add(left: Any, right: Any) -> Expr:
    lhs, rhs = _promote(left), _promote(right)
    if lhs.dimension != rhs.dimension:
        raise DimensionMismatchExprError("Cannot add expressions with different dimensions.")
    return AddExpr(lhs, rhs)


def _dispatch_sub(left: Any, right: Any) -> Expr:
    lhs, rhs = _promote(left), _promote(right)
    if lhs.dimension != rhs.dimension:
        raise DimensionMismatchExprError("Cannot subtract expressions with different dimensions.")
    return SubExpr(lhs, rhs)


def _dispatch_mul(left: Any, right: Any) -> Expr:
    lhs, rhs = _promote(left), _promote(right)
    return MulExpr(lhs, rhs)


def _dispatch_div(left: Any, right: Any) -> Expr:
    lhs, rhs = _promote(left), _promote(right)
    return DivExpr(lhs, rhs)


def _dispatch_pow(left: Any, right: Any) -> Expr:
    base = _promote(left)
    if not isinstance(right, int):
        raise ExprError("Expressions can only be raised to integer powers.")
    return PowExpr(base, right)


@dataclass(frozen=True, slots=True, eq=False)
class QuantityExpr(Expr):
    value: Quantity

    @property
    def dimension(self) -> Dimension:
        return self.value.unit.dimension

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        return frozenset()

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        return self.value


@dataclass(frozen=True, slots=True, eq=False)
class AddExpr(Expr):
    left: Expr
    right: Expr

    @property
    def dimension(self) -> Dimension:
        return self.left.dimension

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        return self.left.free_symbols | self.right.free_symbols

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        return self.left.evaluate(context) + self.right.evaluate(context)


@dataclass(frozen=True, slots=True, eq=False)
class SubExpr(Expr):
    left: Expr
    right: Expr

    @property
    def dimension(self) -> Dimension:
        return self.left.dimension

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        return self.left.free_symbols | self.right.free_symbols

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        return self.left.evaluate(context) - self.right.evaluate(context)


@dataclass(frozen=True, slots=True, eq=False)
class MulExpr(Expr):
    left: Expr
    right: Expr

    @property
    def dimension(self) -> Dimension:
        return self.left.dimension * self.right.dimension

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        return self.left.free_symbols | self.right.free_symbols

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        return self.left.evaluate(context) * self.right.evaluate(context)


@dataclass(frozen=True, slots=True, eq=False)
class DivExpr(Expr):
    left: Expr
    right: Expr

    @property
    def dimension(self) -> Dimension:
        return self.left.dimension / self.right.dimension

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        return self.left.free_symbols | self.right.free_symbols

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        return self.left.evaluate(context) / self.right.evaluate(context)


@dataclass(frozen=True, slots=True, eq=False)
class PowExpr(Expr):
    base: Expr
    power: int

    @property
    def dimension(self) -> Dimension:
        return self.base.dimension**self.power

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        return self.base.free_symbols

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        return self.base.evaluate(context) ** self.power


@dataclass(frozen=True, slots=True, eq=False)
class ConversionExpr(Expr):
    expr: Expr
    target_unit: Unit

    @property
    def dimension(self) -> Dimension:
        return self.target_unit.dimension

    @property
    def free_symbols(self) -> frozenset[Symbol]:
        return self.expr.free_symbols

    def evaluate(self, context: dict[Symbol, Quantity]) -> Quantity:
        return self.expr.evaluate(context).to(self.target_unit)
