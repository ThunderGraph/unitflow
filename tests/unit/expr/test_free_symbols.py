"""Tests for free_symbols on Expr and Constraint AST nodes."""

from __future__ import annotations

from unitflow.catalogs.si import m, s, kg
from unitflow.core.quantities import Quantity
from unitflow.expr.constraints import (
    Conjunction,
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
    MulExpr,
    PowExpr,
    QuantityExpr,
    SubExpr,
)
from unitflow.expr.symbols import Symbol, symbol


class TestExprFreeSymbols:
    def test_symbol_returns_itself(self) -> None:
        x = symbol("x", unit=m)
        assert x.free_symbols == frozenset({x})

    def test_quantity_expr_returns_empty(self) -> None:
        q = QuantityExpr(Quantity(5, m))
        assert q.free_symbols == frozenset()

    def test_add_expr_collects_both_sides(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x + y
        assert isinstance(expr, AddExpr)
        assert expr.free_symbols == frozenset({x, y})

    def test_sub_expr_collects_both_sides(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x - y
        assert isinstance(expr, SubExpr)
        assert expr.free_symbols == frozenset({x, y})

    def test_mul_expr_collects_both_sides(self) -> None:
        force = symbol("F", unit=kg * m / s**2)
        area = symbol("A", unit=m**2)
        expr = force / area
        assert isinstance(expr, DivExpr)
        assert expr.free_symbols == frozenset({force, area})

    def test_div_expr_collects_both_sides(self) -> None:
        x = symbol("x", unit=m)
        t = symbol("t", unit=s)
        expr = x / t
        assert isinstance(expr, DivExpr)
        assert expr.free_symbols == frozenset({x, t})

    def test_pow_expr_collects_base(self) -> None:
        x = symbol("x", unit=m)
        expr = x**2
        assert isinstance(expr, PowExpr)
        assert expr.free_symbols == frozenset({x})

    def test_conversion_expr_collects_inner(self) -> None:
        x = symbol("x", unit=m)
        expr = x.to(m)
        assert isinstance(expr, ConversionExpr)
        assert expr.free_symbols == frozenset({x})

    def test_nested_expr_collects_all_symbols(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        z = symbol("z", unit=m)
        expr = (x + y) * z
        assert expr.free_symbols == frozenset({x, y, z})

    def test_duplicate_symbol_appears_once(self) -> None:
        x = symbol("x", unit=m)
        expr = x + x
        assert expr.free_symbols == frozenset({x})
        assert len(expr.free_symbols) == 1

    def test_same_symbol_instance_used_twice_unifies(self) -> None:
        x = symbol("x", unit=m)
        expr = x + x
        assert len(expr.free_symbols) == 1
        assert x in expr.free_symbols

    def test_quantity_mixed_with_symbol(self) -> None:
        x = symbol("x", unit=m)
        expr = x + Quantity(5, m)
        assert expr.free_symbols == frozenset({x})

    def test_deeply_nested_expr(self) -> None:
        a = symbol("a", unit=m)
        b = symbol("b", unit=m)
        c = symbol("c", unit=s)
        expr = ((a + b) / c) ** 2
        assert expr.free_symbols == frozenset({a, b, c})

    def test_mul_with_scalar(self) -> None:
        x = symbol("x", unit=m)
        expr = x * 3
        assert isinstance(expr, MulExpr)
        assert expr.free_symbols == frozenset({x})


class TestConstraintFreeSymbols:
    def test_equation_collects_both_sides(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        eq = (x == y)
        assert isinstance(eq, Equation)
        assert eq.free_symbols == frozenset({x, y})

    def test_strict_inequality_collects_both_sides(self) -> None:
        x = symbol("x", unit=m)
        c = x < Quantity(10, m)
        assert isinstance(c, StrictInequality)
        assert c.free_symbols == frozenset({x})

    def test_non_strict_inequality_collects_both_sides(self) -> None:
        x = symbol("x", unit=m)
        c = x >= Quantity(0, m)
        assert isinstance(c, NonStrictInequality)
        assert c.free_symbols == frozenset({x})

    def test_conjunction_collects_from_both_branches(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        c = (x > Quantity(0, m)) & (y < Quantity(10, m))
        assert isinstance(c, Conjunction)
        assert c.free_symbols == frozenset({x, y})

    def test_disjunction_collects_from_both_branches(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        c = (x > Quantity(0, m)) | (y < Quantity(10, m))
        assert isinstance(c, Disjunction)
        assert c.free_symbols == frozenset({x, y})

    def test_negation_collects_from_inner(self) -> None:
        x = symbol("x", unit=m)
        eq = x == Quantity(100, m)
        c = ~eq
        assert isinstance(c, Negation)
        assert c.free_symbols == frozenset({x})

    def test_inverted_inequality_collects_symbols(self) -> None:
        x = symbol("x", unit=m)
        c = ~(x > Quantity(100, m))
        assert isinstance(c, NonStrictInequality)
        assert c.free_symbols == frozenset({x})

    def test_compound_constraint_collects_all(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        z = symbol("z", unit=m)
        c = (x > Quantity(0, m)) & (y < Quantity(10, m)) & ~(z == Quantity(5, m))
        assert c.free_symbols == frozenset({x, y, z})

    def test_equation_with_expression_trees(self) -> None:
        shaft_speed = symbol("shaft_speed", unit=s**-1)
        shaft_torque = symbol("shaft_torque", unit=kg * m**2 / s**2)
        shaft_power = symbol("shaft_power", unit=kg * m**2 / s**3)
        eq = shaft_power == shaft_torque * shaft_speed
        assert eq.free_symbols == frozenset({shaft_speed, shaft_torque, shaft_power})

    def test_constraint_with_only_constants_has_no_symbols(self) -> None:
        x = symbol("x", unit=m)
        eq = x == Quantity(5, m)
        assert eq.free_symbols == frozenset({x})
