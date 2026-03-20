from __future__ import annotations

import pytest

from unitflow.catalogs.si import m, s
from unitflow.expr.symbols import symbol
from unitflow.expr.constraints import (
    Equation,
    StrictInequality,
    NonStrictInequality,
    Conjunction,
    Disjunction,
    Negation,
)
from unitflow.expr.errors import BooleanCoercionError


def test_symbolic_comparison_creates_equations_and_inequalities() -> None:
    x = symbol("x", unit=m)
    y = symbol("y", unit=m)

    eq = (x == y)
    assert isinstance(eq, Equation)

    lt = (x < y)
    assert isinstance(lt, StrictInequality)
    assert lt.operator == "<"

    le = (x <= y)
    assert isinstance(le, NonStrictInequality)
    assert le.operator == "<="

    gt = (x > y)
    assert isinstance(gt, StrictInequality)
    assert gt.operator == ">"

    ge = (x >= y)
    assert isinstance(ge, NonStrictInequality)
    assert ge.operator == ">="


def test_constraint_logical_composition() -> None:
    x = symbol("x", unit=m)
    c1 = x > 0 * m
    c2 = x < 10 * m

    conj = c1 & c2
    assert isinstance(conj, Conjunction)
    assert conj.left.is_same(c1)
    assert conj.right.is_same(c2)

    disj = c1 | c2
    assert isinstance(disj, Disjunction)


def test_constraint_negation() -> None:
    x = symbol("x", unit=m)

    # Invert strict < -> non-strict >=
    c1 = x < 10 * m
    inv1 = ~c1
    assert isinstance(inv1, NonStrictInequality)
    assert inv1.operator == ">="

    # Invert non-strict <= -> strict >
    c2 = x <= 10 * m
    inv2 = ~c2
    assert isinstance(inv2, StrictInequality)
    assert inv2.operator == ">"

    # Invert equation -> negation of equation
    c3 = x == 10 * m
    inv3 = ~c3
    assert isinstance(inv3, Negation)


def test_constraint_boolean_coercion_raises() -> None:
    x = symbol("x", unit=m)
    c = x == 10 * m

    with pytest.raises(BooleanCoercionError):
        bool(c)

    with pytest.raises(BooleanCoercionError):
        if c:
            pass

    with pytest.raises(BooleanCoercionError):
        _ = c and (x < 20 * m)
