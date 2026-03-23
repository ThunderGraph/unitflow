"""Errors for the expression layer."""

from unitflow.errors import UnitflowError


class ExprError(UnitflowError):
    """Raised for general expression and symbolic errors."""

class DimensionMismatchExprError(ExprError):
    """Raised when expressions have mismatched dimensions in operations."""

class BooleanCoercionError(ExprError):
    """Raised when a constraint is coerced to boolean."""

class EvaluationError(ExprError):
    """Raised when expression evaluation fails (e.g. unbound symbol)."""

class CompilationError(ExprError):
    """Raised when numeric compilation of an expression fails."""
