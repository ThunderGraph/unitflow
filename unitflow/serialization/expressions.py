"""Serialization for expression and constraint trees."""

from __future__ import annotations

from typing import Any

from unitflow.errors import SerializationError
from unitflow.expr.constraints import (
    Conjunction,
    Constraint,
    Disjunction,
    Equation,
    Negation,
    NonStrictInequality,
    StrictInequality,
)
from unitflow.expr.expressions import (
    AddExpr,
    ConversionExpr,
    DivExpr,
    Expr,
    MulExpr,
    PowExpr,
    QuantityExpr,
    SubExpr,
)
from unitflow.expr.symbols import Symbol
from unitflow.serialization.quantities import (
    deserialize_dimension,
    deserialize_quantity,
    deserialize_unit,
    serialize_dimension,
    serialize_quantity,
    serialize_unit,
)


def serialize_expr(expr: Expr) -> dict[str, Any]:
    if isinstance(expr, Symbol):
        return {
            "type": "Symbol",
            "name": expr.name,
            "dimension": serialize_dimension(expr.dimension),
            "unit": serialize_unit(expr.unit) if expr.unit else None,
            "quantity_kind": expr.quantity_kind,
        }
    elif isinstance(expr, QuantityExpr):
        return {
            "type": "QuantityExpr",
            "value": serialize_quantity(expr.value),
        }
    elif isinstance(expr, AddExpr):
        return {
            "type": "AddExpr",
            "left": serialize_expr(expr.left),
            "right": serialize_expr(expr.right),
        }
    elif isinstance(expr, SubExpr):
        return {
            "type": "SubExpr",
            "left": serialize_expr(expr.left),
            "right": serialize_expr(expr.right),
        }
    elif isinstance(expr, MulExpr):
        return {
            "type": "MulExpr",
            "left": serialize_expr(expr.left),
            "right": serialize_expr(expr.right),
        }
    elif isinstance(expr, DivExpr):
        return {
            "type": "DivExpr",
            "left": serialize_expr(expr.left),
            "right": serialize_expr(expr.right),
        }
    elif isinstance(expr, PowExpr):
        return {
            "type": "PowExpr",
            "base": serialize_expr(expr.base),
            "power": expr.power,
        }
    elif isinstance(expr, ConversionExpr):
        return {
            "type": "ConversionExpr",
            "expr": serialize_expr(expr.expr),
            "target_unit": serialize_unit(expr.target_unit),
        }
    raise SerializationError(f"Unsupported expression type: {type(expr)}")


def deserialize_expr(data: dict[str, Any]) -> Expr:
    try:
        expr_type = data["type"]
        if expr_type == "Symbol":
            return Symbol(
                name=data["name"],
                _dimension=deserialize_dimension(data["dimension"]),
                unit=deserialize_unit(data["unit"]) if data.get("unit") else None,
                quantity_kind=data.get("quantity_kind"),
            )
        elif expr_type == "QuantityExpr":
            return QuantityExpr(value=deserialize_quantity(data["value"]))
        elif expr_type == "AddExpr":
            return AddExpr(left=deserialize_expr(data["left"]), right=deserialize_expr(data["right"]))
        elif expr_type == "SubExpr":
            return SubExpr(left=deserialize_expr(data["left"]), right=deserialize_expr(data["right"]))
        elif expr_type == "MulExpr":
            return MulExpr(left=deserialize_expr(data["left"]), right=deserialize_expr(data["right"]))
        elif expr_type == "DivExpr":
            return DivExpr(left=deserialize_expr(data["left"]), right=deserialize_expr(data["right"]))
        elif expr_type == "PowExpr":
            return PowExpr(base=deserialize_expr(data["base"]), power=int(data["power"]))
        elif expr_type == "ConversionExpr":
            return ConversionExpr(
                expr=deserialize_expr(data["expr"]),
                target_unit=deserialize_unit(data["target_unit"]),
            )
        raise SerializationError(f"Unknown expression type: {expr_type}")
    except KeyError as exc:
        raise SerializationError(f"Missing key in expression data: {exc}") from exc


def serialize_constraint(constraint: Constraint) -> dict[str, Any]:
    if isinstance(constraint, Equation):
        return {
            "type": "Equation",
            "left": serialize_expr(constraint.left),
            "right": serialize_expr(constraint.right),
        }
    elif isinstance(constraint, StrictInequality):
        return {
            "type": "StrictInequality",
            "left": serialize_expr(constraint.left),
            "right": serialize_expr(constraint.right),
            "operator": constraint.operator,
        }
    elif isinstance(constraint, NonStrictInequality):
        return {
            "type": "NonStrictInequality",
            "left": serialize_expr(constraint.left),
            "right": serialize_expr(constraint.right),
            "operator": constraint.operator,
        }
    elif isinstance(constraint, Conjunction):
        return {
            "type": "Conjunction",
            "left": serialize_constraint(constraint.left),
            "right": serialize_constraint(constraint.right),
        }
    elif isinstance(constraint, Disjunction):
        return {
            "type": "Disjunction",
            "left": serialize_constraint(constraint.left),
            "right": serialize_constraint(constraint.right),
        }
    elif isinstance(constraint, Negation):
        return {
            "type": "Negation",
            "constraint": serialize_constraint(constraint.constraint),
        }
    raise SerializationError(f"Unsupported constraint type: {type(constraint)}")


def deserialize_constraint(data: dict[str, Any]) -> Constraint:
    try:
        constraint_type = data["type"]
        if constraint_type == "Equation":
            return Equation(
                left=deserialize_expr(data["left"]),
                right=deserialize_expr(data["right"]),
            )
        elif constraint_type == "StrictInequality":
            return StrictInequality(
                left=deserialize_expr(data["left"]),
                right=deserialize_expr(data["right"]),
                operator=data["operator"],
            )
        elif constraint_type == "NonStrictInequality":
            return NonStrictInequality(
                left=deserialize_expr(data["left"]),
                right=deserialize_expr(data["right"]),
                operator=data["operator"],
            )
        elif constraint_type == "Conjunction":
            return Conjunction(
                left=deserialize_constraint(data["left"]),
                right=deserialize_constraint(data["right"]),
            )
        elif constraint_type == "Disjunction":
            return Disjunction(
                left=deserialize_constraint(data["left"]),
                right=deserialize_constraint(data["right"]),
            )
        elif constraint_type == "Negation":
            return Negation(constraint=deserialize_constraint(data["constraint"]))
        raise SerializationError(f"Unknown constraint type: {constraint_type}")
    except KeyError as exc:
        raise SerializationError(f"Missing key in constraint data: {exc}") from exc
