"""Constraint nodes and logic composition for the expression layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from unitflow.expr.errors import BooleanCoercionError

if TYPE_CHECKING:
    from unitflow.expr.expressions import Expr


class Constraint:
    """Base class for all symbolic constraints."""

    def __bool__(self) -> bool:
        raise BooleanCoercionError(
            "Constraints are not booleans. Use logical composition (& and |)."
        )

    def __and__(self, other: Any) -> Constraint:
        if not isinstance(other, Constraint):
            return NotImplemented
        return Conjunction(self, other)

    def __or__(self, other: Any) -> Constraint:
        if not isinstance(other, Constraint):
            return NotImplemented
        return Disjunction(self, other)

    def __invert__(self) -> Constraint:
        return Negation(self)

    def is_same(self, other: Any) -> bool:
        """Check if this constraint is structurally identical to another."""
        if type(self) is not type(other):
            return False
        if hasattr(self, "__dataclass_fields__"):
            for field in self.__dataclass_fields__:
                val1 = getattr(self, field)
                val2 = getattr(other, field)

                # Check is_same if it's an Expr or Constraint
                if hasattr(val1, "is_same") and hasattr(val2, "is_same"):
                    if not val1.is_same(val2):
                        return False
                else:
                    if val1 != val2:
                        return False
            return True
        return self is other


@dataclass(frozen=True, slots=True, eq=False)
class Equation(Constraint):
    left: Expr
    right: Expr

    def __invert__(self) -> Constraint:
        return Negation(self)


@dataclass(frozen=True, slots=True, eq=False)
class StrictInequality(Constraint):
    left: Expr
    right: Expr
    operator: str  # "<" or ">"

    def __post_init__(self) -> None:
        if self.operator not in ("<", ">"):
            raise ValueError(f"StrictInequality operator must be '<' or '>', got {self.operator!r}")

    def __invert__(self) -> Constraint:
        if self.operator == "<":
            return NonStrictInequality(self.left, self.right, ">=")
        return NonStrictInequality(self.left, self.right, "<=")


@dataclass(frozen=True, slots=True, eq=False)
class NonStrictInequality(Constraint):
    left: Expr
    right: Expr
    operator: str  # "<=" or ">="

    def __post_init__(self) -> None:
        if self.operator not in ("<=", ">="):
            raise ValueError(f"NonStrictInequality operator must be '<=' or '>=', got {self.operator!r}")

    def __invert__(self) -> Constraint:
        if self.operator == "<=":
            return StrictInequality(self.left, self.right, ">")
        return StrictInequality(self.left, self.right, "<")


@dataclass(frozen=True, slots=True, eq=False)
class Conjunction(Constraint):
    left: Constraint
    right: Constraint


@dataclass(frozen=True, slots=True, eq=False)
class Disjunction(Constraint):
    left: Constraint
    right: Constraint


@dataclass(frozen=True, slots=True, eq=False)
class Negation(Constraint):
    constraint: Constraint
