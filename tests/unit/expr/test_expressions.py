from __future__ import annotations

import pytest
from fractions import Fraction

from unitflow import Quantity, DimensionMismatchError
from unitflow.catalogs.si import m, s, kg, N
from unitflow.expr.symbols import symbol
from unitflow.expr.expressions import (
    Expr,
    QuantityExpr,
    AddExpr,
    MulExpr,
    DivExpr,
    PowExpr,
    ConversionExpr,
)
from unitflow.expr.errors import DimensionMismatchExprError, ExprError


def test_symbol_requires_name_and_semantics() -> None:
    with pytest.raises(ExprError):
        symbol("", unit=m)
    with pytest.raises(ExprError):
        symbol("x")


def test_symbol_dimension_and_unit_must_agree() -> None:
    with pytest.raises(ExprError):
        symbol("x", dimension=s.dimension, unit=m)


def test_symbol_construction_stores_correct_metadata() -> None:
    speed = symbol("v", unit=m / s)
    assert speed.dimension == (m / s).dimension
    assert speed.unit == m / s


def test_quantity_promotes_to_expr_in_arithmetic() -> None:
    x = symbol("x", unit=m)
    q = Quantity(5, m)

    # Quantity op Symbol
    res1 = q + x
    assert isinstance(res1, AddExpr)
    assert isinstance(res1.left, QuantityExpr)
    assert res1.left.value == q
    assert res1.right is x

    # Symbol op Quantity
    res2 = x * q
    assert isinstance(res2, MulExpr)
    assert res2.left is x
    assert isinstance(res2.right, QuantityExpr)
    assert res2.right.value == q

    # Quantity op Symbol (Multiplication)
    res3 = q * x
    assert isinstance(res3, MulExpr)
    assert isinstance(res3.left, QuantityExpr)
    assert res3.left.value == q
    assert res3.right is x

    # Quantity op Symbol (Division)
    res4 = q / x
    assert isinstance(res4, DivExpr)
    assert isinstance(res4.left, QuantityExpr)
    assert res4.left.value == q
    assert res4.right is x


def test_dimension_mismatch_raises_in_expr_addition() -> None:
    x = symbol("x", unit=m)
    t = symbol("t", unit=s)

    with pytest.raises(DimensionMismatchExprError):
        _ = x + t


def test_expr_multiplication_and_division() -> None:
    x = symbol("x", unit=m)
    t = symbol("t", unit=s)

    v = x / t
    assert isinstance(v, DivExpr)
    assert v.dimension == m.dimension / s.dimension

    area = x * x
    assert isinstance(area, MulExpr)
    assert area.dimension == m.dimension**2


def test_expr_pow_validates_power() -> None:
    x = symbol("x", unit=m)

    x2 = x**2
    assert isinstance(x2, PowExpr)
    assert x2.dimension == m.dimension**2

    with pytest.raises(ExprError):
        _ = x**2.5


def test_expr_is_same_structural_equality() -> None:
    x1 = symbol("x", unit=m)
    x2 = symbol("x", unit=m)
    y = symbol("y", unit=m)

    assert x1.is_same(x2)
    assert not x1.is_same(y)

    expr1 = x1 * 2 + y
    expr2 = x2 * 2 + symbol("y", unit=m)
    
    assert expr1.is_same(expr2)

def test_expr_to_returns_conversion_expr() -> None:
    x = symbol("x", unit=m)
    converted = x.to(m)
    
    assert isinstance(converted, ConversionExpr)
    assert converted.dimension == m.dimension
    
    with pytest.raises(DimensionMismatchExprError):
        x.to(s)
