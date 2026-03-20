from __future__ import annotations

from unitflow import Quantity
from unitflow.catalogs.si import N, Pa, m
from unitflow.expr.constraints import Conjunction, Equation
from unitflow.expr.expressions import Expr
from unitflow.expr.symbols import symbol


def test_phase6_acceptance_pressure_area_promotes_to_expr() -> None:
    # `pressure * area` promotes to `Expr`, not `Quantity`
    area = 2 * m**2
    pressure = symbol("pressure", unit=Pa)
    force = pressure * area

    assert isinstance(force, Expr)
    assert not isinstance(force, Quantity)
    assert force.dimension == (Pa * m**2).dimension


def test_phase6_acceptance_comparison_dispatch_symmetry() -> None:
    # `5 * si.N == force` and `force == 5 * si.N` produce equivalent constraint objects
    force = symbol("force", unit=N)
    five_newtons = 5 * N

    eq1 = force == five_newtons
    eq2 = five_newtons == force

    assert isinstance(eq1, Equation)
    assert isinstance(eq2, Equation)

    # Python translates `Quantity == Symbol` to `Quantity.__eq__(Symbol)`.
    # That returns NotImplemented, so Python calls `Symbol.__eq__(Quantity)`.
    # This results in `Equation(force, QuantityExpr(5 N))` in both cases.
    assert eq1.is_same(eq2)


def test_phase6_acceptance_inspectable_conjunction_tree() -> None:
    # `(0 <= x) & (x <= 10)` produces an inspectable conjunction tree
    x = symbol("x", unit=m)
    bounds = (0 * m <= x) & (x <= 10 * m)

    assert isinstance(bounds, Conjunction)
    assert bounds.left.is_same(0 * m <= x)
    assert bounds.right.is_same(x <= 10 * m)


def test_phase6_acceptance_comparison_dispatch_without_concrete_quantity_knowing_symbolic() -> None:
    # comparison dispatch works without forcing concrete quantity code to know the full symbolic implementation in advance
    # Because `Quantity.__eq__` returns `NotImplemented` for unknown types, it automatically falls back to `Symbol.__eq__`.
    x = symbol("x", unit=m)
    q = Quantity(5, m)

    eq = q == x
    assert isinstance(eq, Equation)

    eq_ineq = q < x
    assert eq_ineq.operator == ">"  # `q < x` calls `x.__gt__(q)` returning `x > q`

