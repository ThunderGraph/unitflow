from __future__ import annotations

from unitflow import Quantity
from unitflow.catalogs.si import m, s
from unitflow.expr.symbols import symbol
from unitflow.expr.expressions import ConversionExpr, QuantityExpr
from unitflow.serialization.expressions import (
    serialize_expr,
    deserialize_expr,
    serialize_constraint,
    deserialize_constraint,
)


def test_symbol_serialization_roundtrip() -> None:
    x = symbol("x", unit=m, quantity_kind="length")
    data = serialize_expr(x)
    restored = deserialize_expr(data)
    assert restored.is_same(x)


def test_expr_tree_serialization_roundtrip() -> None:
    x = symbol("x", unit=m)
    y = symbol("y", unit=s)
    expr = (x * 2 + QuantityExpr(Quantity(5, m))) / (y ** 2)
    
    data = serialize_expr(expr)
    restored = deserialize_expr(data)
    assert restored.is_same(expr)


def test_conversion_expr_serialization_roundtrip() -> None:
    x = symbol("x", unit=m)
    expr = ConversionExpr(x, m)
    
    data = serialize_expr(expr)
    restored = deserialize_expr(data)
    assert restored.is_same(expr)


def test_constraint_tree_serialization_roundtrip() -> None:
    x = symbol("x", unit=m)
    c1 = x > 0 * m
    c2 = x <= 10 * m
    c3 = ~(x == 5 * m)
    
    constraint = (c1 & c2) | c3
    data = serialize_constraint(constraint)
    restored = deserialize_constraint(data)
    
    assert restored.is_same(constraint)
