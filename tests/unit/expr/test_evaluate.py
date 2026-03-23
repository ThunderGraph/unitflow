"""Tests for evaluate(context) on Expr and Constraint AST nodes."""

from __future__ import annotations

import pytest

from unitflow.catalogs.mechanical import rpm
from unitflow.catalogs.si import N, W, kg, m, s
from unitflow.core.quantities import Quantity
from unitflow.expr.errors import EvaluationError
from unitflow.expr.expressions import QuantityExpr
from unitflow.expr.symbols import symbol


class TestExprEvaluate:
    def test_symbol_evaluates_from_context(self) -> None:
        x = symbol("x", unit=m)
        result = x.evaluate({x: Quantity(5, m)})
        assert result == Quantity(5, m)

    def test_symbol_missing_from_context_raises(self) -> None:
        x = symbol("x", unit=m)
        with pytest.raises(EvaluationError, match="'x'"):
            x.evaluate({})

    def test_quantity_expr_ignores_context(self) -> None:
        q = QuantityExpr(Quantity(42, m))
        result = q.evaluate({})
        assert result == Quantity(42, m)

    def test_add_expr(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x + y
        result = expr.evaluate({x: Quantity(3, m), y: Quantity(7, m)})
        assert result == Quantity(10, m)

    def test_sub_expr(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x - y
        result = expr.evaluate({x: Quantity(10, m), y: Quantity(3, m)})
        assert result == Quantity(7, m)

    def test_mul_expr(self) -> None:
        force = symbol("F", unit=N)
        dist = symbol("d", unit=m)
        expr = force * dist
        ctx = {force: Quantity(10, N), dist: Quantity(5, m)}
        result = expr.evaluate(ctx)
        assert result == Quantity(50, N * m)

    def test_div_expr(self) -> None:
        x = symbol("x", unit=m)
        t = symbol("t", unit=s)
        expr = x / t
        result = expr.evaluate({x: Quantity(100, m), t: Quantity(10, s)})
        assert result == Quantity(10, m / s)

    def test_pow_expr(self) -> None:
        x = symbol("x", unit=m)
        expr = x ** 2
        result = expr.evaluate({x: Quantity(3, m)})
        assert result == Quantity(9, m ** 2)

    def test_conversion_expr(self) -> None:
        from unitflow.catalogs.si import cm
        x = symbol("x", unit=cm)
        expr = x.to(m)
        result = expr.evaluate({x: Quantity(200, cm)})
        assert result.is_close(Quantity(2, m))

    def test_nested_expression(self) -> None:
        a = symbol("a", unit=m)
        b = symbol("b", unit=m)
        expr = (a + b) * Quantity(2, m / m)
        ctx = {a: Quantity(3, m), b: Quantity(7, m)}
        result = expr.evaluate(ctx)
        assert result == Quantity(20, m)

    def test_expression_with_constants_and_symbols(self) -> None:
        x = symbol("x", unit=m)
        expr = x + Quantity(5, m)
        result = expr.evaluate({x: Quantity(10, m)})
        assert result == Quantity(15, m)

    def test_realistic_power_equation(self) -> None:
        shaft_torque = symbol("T", unit=N * m)
        shaft_speed = symbol("w", unit=m / (m * s))
        expr = shaft_torque * shaft_speed
        ctx = {
            shaft_torque: Quantity(50, N * m),
            shaft_speed: Quantity(100, m / (m * s)),
        }
        result = expr.evaluate(ctx)
        assert result.is_close(Quantity(5000, N * m / s))

    def test_deeply_nested_evaluation(self) -> None:
        a = symbol("a", unit=m)
        b = symbol("b", unit=m)
        c = symbol("c", unit=s)
        expr = ((a + b) / c) ** 2
        ctx = {a: Quantity(3, m), b: Quantity(7, m), c: Quantity(2, s)}
        result = expr.evaluate(ctx)
        assert result.is_close(Quantity(25, (m / s) ** 2))


class TestConstraintEvaluate:
    def test_equation_true_when_equal(self) -> None:
        x = symbol("x", unit=m)
        eq = x == Quantity(5, m)
        assert eq.evaluate({x: Quantity(5, m)}) is True

    def test_equation_false_when_unequal(self) -> None:
        x = symbol("x", unit=m)
        eq = x == Quantity(5, m)
        assert eq.evaluate({x: Quantity(6, m)}) is False

    def test_equation_uses_tolerance(self) -> None:
        x = symbol("x", unit=m)
        eq = x == Quantity(5, m)
        assert eq.evaluate({x: Quantity(5.0000000001, m)}) is True
        assert eq.evaluate({x: Quantity(5.1, m)}) is False

    def test_equation_custom_tolerance(self) -> None:
        x = symbol("x", unit=m)
        eq = x == Quantity(5, m)
        assert eq.evaluate({x: Quantity(5.05, m)}, rel_tol=0.1) is True
        assert eq.evaluate({x: Quantity(5.05, m)}, rel_tol=0.001) is False

    def test_equation_abs_tolerance(self) -> None:
        x = symbol("x", unit=m)
        eq = x == Quantity(0, m)
        assert eq.evaluate({x: Quantity(0.001, m)}, abs_tol=0.01) is True
        assert eq.evaluate({x: Quantity(0.1, m)}, abs_tol=0.01) is False

    def test_strict_less_than(self) -> None:
        x = symbol("x", unit=m)
        c = x < Quantity(10, m)
        assert c.evaluate({x: Quantity(5, m)}) is True
        assert c.evaluate({x: Quantity(10, m)}) is False
        assert c.evaluate({x: Quantity(15, m)}) is False

    def test_strict_greater_than(self) -> None:
        x = symbol("x", unit=m)
        c = x > Quantity(10, m)
        assert c.evaluate({x: Quantity(15, m)}) is True
        assert c.evaluate({x: Quantity(10, m)}) is False
        assert c.evaluate({x: Quantity(5, m)}) is False

    def test_non_strict_less_equal(self) -> None:
        x = symbol("x", unit=m)
        c = x <= Quantity(10, m)
        assert c.evaluate({x: Quantity(5, m)}) is True
        assert c.evaluate({x: Quantity(10, m)}) is True
        assert c.evaluate({x: Quantity(15, m)}) is False

    def test_non_strict_greater_equal(self) -> None:
        x = symbol("x", unit=m)
        c = x >= Quantity(10, m)
        assert c.evaluate({x: Quantity(15, m)}) is True
        assert c.evaluate({x: Quantity(10, m)}) is True
        assert c.evaluate({x: Quantity(5, m)}) is False

    def test_conjunction_both_true(self) -> None:
        x = symbol("x", unit=m)
        c = (x > Quantity(0, m)) & (x < Quantity(10, m))
        assert c.evaluate({x: Quantity(5, m)}) is True

    def test_conjunction_one_false(self) -> None:
        x = symbol("x", unit=m)
        c = (x > Quantity(0, m)) & (x < Quantity(10, m))
        assert c.evaluate({x: Quantity(15, m)}) is False

    def test_conjunction_short_circuits(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        c = (x > Quantity(100, m)) & (y < Quantity(10, m))
        assert c.evaluate({x: Quantity(5, m), y: Quantity(5, m)}) is False

    def test_disjunction_one_true(self) -> None:
        x = symbol("x", unit=m)
        c = (x < Quantity(0, m)) | (x > Quantity(10, m))
        assert c.evaluate({x: Quantity(15, m)}) is True

    def test_disjunction_both_false(self) -> None:
        x = symbol("x", unit=m)
        c = (x < Quantity(0, m)) | (x > Quantity(10, m))
        assert c.evaluate({x: Quantity(5, m)}) is False

    def test_negation(self) -> None:
        x = symbol("x", unit=m)
        eq = x == Quantity(5, m)
        neg = ~eq
        assert neg.evaluate({x: Quantity(5, m)}) is False
        assert neg.evaluate({x: Quantity(6, m)}) is True

    def test_compound_constraint(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        c = (x >= Quantity(0, m)) & (x <= Quantity(100, m)) & (y > Quantity(0, m))
        ctx = {x: Quantity(50, m), y: Quantity(1, m)}
        assert c.evaluate(ctx) is True

    def test_equation_with_expression_trees(self) -> None:
        torque = symbol("T", unit=N * m)
        speed = symbol("w", unit=m / (m * s))
        power = symbol("P", unit=N * m / s)
        eq = power == torque * speed
        ctx = {
            torque: Quantity(50, N * m),
            speed: Quantity(100, m / (m * s)),
            power: Quantity(5000, N * m / s),
        }
        assert eq.evaluate(ctx) is True

    def test_equation_with_expression_trees_fails(self) -> None:
        torque = symbol("T", unit=N * m)
        speed = symbol("w", unit=m / (m * s))
        power = symbol("P", unit=N * m / s)
        eq = power == torque * speed
        ctx = {
            torque: Quantity(50, N * m),
            speed: Quantity(100, m / (m * s)),
            power: Quantity(9999, N * m / s),
        }
        assert eq.evaluate(ctx) is False

    def test_missing_symbol_in_constraint_raises(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        c = x < y
        with pytest.raises(EvaluationError, match="'y'"):
            c.evaluate({x: Quantity(5, m)})
