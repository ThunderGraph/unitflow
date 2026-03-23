"""Integration tests for evaluate() across realistic engineering workflows."""

from __future__ import annotations

import pytest

from unitflow.catalogs.mechanical import rpm
from unitflow.catalogs.si import N, W, kg, m, s, rad
from unitflow.core.quantities import Quantity
from unitflow.expr.errors import BooleanCoercionError, EvaluationError
from unitflow.expr.symbols import symbol


class TestRealisticEngineeringEvaluation:
    """End-to-end evaluation of a realistic multi-symbol engineering model."""

    def test_shaft_power_model(self) -> None:
        torque = symbol("shaft_torque", unit=N * m)
        speed = symbol("shaft_speed", unit=rad / s)
        power_expr = torque * speed

        ctx = {
            torque: Quantity(50, N * m),
            speed: Quantity(314, rad / s),
        }
        result = power_expr.evaluate(ctx)
        assert result.is_close(Quantity(15700, N * m / s), rel_tol=1e-6)

    def test_power_balance_constraint_passes(self) -> None:
        torque = symbol("shaft_torque", unit=N * m)
        speed = symbol("shaft_speed", unit=rad / s)
        power = symbol("shaft_power", unit=N * m / s)

        constraint = power == torque * speed

        ctx = {
            torque: Quantity(50, N * m),
            speed: Quantity(100, rad / s),
            power: Quantity(5000, N * m / s),
        }
        assert constraint.evaluate(ctx) is True

    def test_power_balance_constraint_fails(self) -> None:
        torque = symbol("shaft_torque", unit=N * m)
        speed = symbol("shaft_speed", unit=rad / s)
        power = symbol("shaft_power", unit=N * m / s)

        constraint = power == torque * speed

        ctx = {
            torque: Quantity(50, N * m),
            speed: Quantity(100, rad / s),
            power: Quantity(9999, N * m / s),
        }
        assert constraint.evaluate(ctx) is False

    def test_bounded_constraint_model(self) -> None:
        temp = symbol("operating_temp", unit=m / m)
        max_temp = symbol("max_temp", unit=m / m)

        constraint = (temp >= Quantity(0, m / m)) & (temp < max_temp)

        ctx = {temp: Quantity(85, m / m), max_temp: Quantity(150, m / m)}
        assert constraint.evaluate(ctx) is True

        ctx_hot = {temp: Quantity(200, m / m), max_temp: Quantity(150, m / m)}
        assert constraint.evaluate(ctx_hot) is False


class TestSymbolIdentityContract:
    """Verify that evaluate requires the same Symbol instances, not structural copies."""

    def test_same_instance_works(self) -> None:
        x = symbol("x", unit=m)
        expr = x + Quantity(1, m)
        assert expr.evaluate({x: Quantity(5, m)}) == Quantity(6, m)

    def test_different_instance_same_structure_fails(self) -> None:
        x1 = symbol("x", unit=m)
        x2 = symbol("x", unit=m)
        expr = x1 + Quantity(1, m)
        with pytest.raises(EvaluationError, match="'x'"):
            expr.evaluate({x2: Quantity(5, m)})

    def test_free_symbols_provides_correct_keys(self) -> None:
        x = symbol("x", unit=m)
        y = symbol("y", unit=m)
        expr = x + y
        ctx = {sym: Quantity(1, m) for sym in expr.free_symbols}
        result = expr.evaluate(ctx)
        assert result == Quantity(2, m)
