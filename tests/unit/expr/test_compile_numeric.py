"""Tests for compile_numeric and compile_residual."""

from __future__ import annotations

import math

import pytest

from unitflow.catalogs.si import N, kg, m, rad, s
from unitflow.core.quantities import Quantity
from unitflow.expr.compile import compile_numeric, compile_residual
from unitflow.expr.errors import CompilationError
from unitflow.expr.symbols import symbol


class TestCompileNumericBasics:
    def test_single_symbol_identity(self) -> None:
        x = symbol("x", unit=m)
        fn = compile_numeric(x, [x], {x: m})
        assert fn(5.0) == 5.0

    def test_constant_expression(self) -> None:
        x = symbol("x", unit=m)
        expr = x + Quantity(3, m)
        fn = compile_numeric(expr, [x], {x: m})
        assert fn(7.0) == pytest.approx(10.0)

    def test_add(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x + y
        fn = compile_numeric(expr, [x, y], {x: m, y: m})
        assert fn(3.0, 7.0) == pytest.approx(10.0)

    def test_sub(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x - y
        fn = compile_numeric(expr, [x, y], {x: m, y: m})
        assert fn(10.0, 3.0) == pytest.approx(7.0)

    def test_mul(self) -> None:
        force = symbol("F", unit=N)
        dist = symbol("d", unit=m)
        expr = force * dist
        fn = compile_numeric(expr, [force, dist], {force: N, dist: m})
        assert fn(10.0, 5.0) == pytest.approx(50.0)

    def test_div(self) -> None:
        x = symbol("x", unit=m)
        t = symbol("t", unit=s)
        expr = x / t
        fn = compile_numeric(expr, [x, t], {x: m, t: s})
        assert fn(100.0, 10.0) == pytest.approx(10.0)

    def test_pow(self) -> None:
        x = symbol("x", unit=m)
        expr = x ** 2
        fn = compile_numeric(expr, [x], {x: m})
        assert fn(3.0) == pytest.approx(9.0)

    def test_nested_expression(self) -> None:
        a = symbol("a", unit=m)
        b = symbol("b", unit=m)
        c = symbol("c", unit=s)
        expr = ((a + b) / c) ** 2
        fn = compile_numeric(expr, [a, b, c], {a: m, b: m, c: s})
        assert fn(3.0, 7.0, 2.0) == pytest.approx(25.0)


class TestCompileNumericConstants:
    def test_quantity_constant_baked_in(self) -> None:
        x = symbol("x", unit=m)
        expr = x * Quantity(2, m / m)
        fn = compile_numeric(expr, [x], {x: m})
        assert fn(5.0) == pytest.approx(10.0)

    def test_multiple_constants(self) -> None:
        x = symbol("x", unit=m)
        expr = (x + Quantity(1, m)) * Quantity(3, m / m)
        fn = compile_numeric(expr, [x], {x: m})
        assert fn(4.0) == pytest.approx(15.0)


class TestCompileNumericConversion:
    def test_conversion_expr_bakes_scale_factor(self) -> None:
        from unitflow.catalogs.si import cm
        x = symbol("x", unit=cm)
        expr = x.to(m)
        fn = compile_numeric(expr, [x], {x: cm})
        assert fn(200.0) == pytest.approx(2.0, rel=1e-6)


class TestCompileNumericValidation:
    def test_missing_symbol_raises(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x + y
        with pytest.raises(CompilationError, match="'y'"):
            compile_numeric(expr, [x], {x: m})

    def test_missing_reference_unit_raises(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x + y
        with pytest.raises(CompilationError, match="'y'"):
            compile_numeric(expr, [x, y], {x: m})


class TestCompileNumericMatchesEvaluate:
    def test_agrees_with_evaluate(self) -> None:
        torque = symbol("T", unit=N * m)
        speed = symbol("w", unit=rad / s)
        expr = torque * speed

        fn = compile_numeric(expr, [torque, speed], {torque: N * m, speed: rad / s})
        compiled_result = fn(50.0, 314.0)

        ctx = {torque: Quantity(50, N * m), speed: Quantity(314, rad / s)}
        eval_result = expr.evaluate(ctx)

        assert compiled_result == pytest.approx(float(eval_result.magnitude), rel=1e-9)


class TestCompileResidual:
    def test_residual_at_solution_is_zero(self) -> None:
        torque = symbol("T", unit=N * m)
        speed = symbol("w", unit=rad / s)
        power = symbol("P", unit=N * m / s)
        eq = power == torque * speed

        fn = compile_residual(eq, [power, torque, speed], {power: N * m / s, torque: N * m, speed: rad / s})
        assert fn(5000.0, 50.0, 100.0) == pytest.approx(0.0)

    def test_residual_nonzero_when_wrong(self) -> None:
        torque = symbol("T", unit=N * m)
        speed = symbol("w", unit=rad / s)
        power = symbol("P", unit=N * m / s)
        eq = power == torque * speed

        fn = compile_residual(eq, [power, torque, speed], {power: N * m / s, torque: N * m, speed: rad / s})
        residual = fn(9999.0, 50.0, 100.0)
        assert abs(residual) > 1.0

    def test_residual_rejects_non_equation(self) -> None:
        x = symbol("x", unit=m)
        ineq = x < Quantity(10, m)
        with pytest.raises(CompilationError, match="Equation"):
            compile_residual(ineq, [x], {x: m})  # type: ignore[arg-type]

    def test_residual_agrees_with_evaluate(self) -> None:
        a = symbol("a", unit=m)
        b = symbol("b", unit=m)
        eq = a == b * Quantity(2, m / m)

        fn = compile_residual(eq, [a, b], {a: m, b: m})
        assert fn(10.0, 5.0) == pytest.approx(0.0)
        assert fn(10.0, 6.0) != pytest.approx(0.0)


class TestCompileNumericPerformance:
    def test_compiled_is_callable_many_times(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = (x + y) ** 2
        fn = compile_numeric(expr, [x, y], {x: m, y: m})
        results = [fn(float(i), float(i + 1)) for i in range(1000)]
        assert len(results) == 1000
        assert results[0] == pytest.approx((0.0 + 1.0) ** 2)
        assert results[999] == pytest.approx((999.0 + 1000.0) ** 2)
