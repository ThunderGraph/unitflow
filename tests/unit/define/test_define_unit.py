from __future__ import annotations

from fractions import Fraction

import pytest

from unitflow import Quantity, Scale, UnitError, define_unit, m


def test_define_unit_from_exact_quantity_expr() -> None:
    centimeter = define_unit(
        name="centimeter_test",
        symbol="cm_test",
        expr=Quantity(Fraction(1, 100), m),
    )

    assert centimeter.dimension == m.dimension
    assert centimeter.scale == m.scale * Scale.from_ratio(1, 100)


def test_define_unit_from_plain_unit_expr() -> None:
    renamed_meter = define_unit(name="meter_test", symbol="m_test", expr=m)

    assert renamed_meter.dimension == m.dimension
    assert renamed_meter.scale == m.scale


def test_define_unit_from_integer_quantity_expr() -> None:
    kilo_meter = define_unit(name="kilometer_test", symbol="km_test", expr=Quantity(1000, m))

    assert kilo_meter.dimension == m.dimension
    assert kilo_meter.scale == m.scale * Scale.from_int(1000)


def test_define_unit_rejects_float_quantity_expr() -> None:
    with pytest.raises(UnitError):
        define_unit(name="bad_unit", symbol="bad", expr=Quantity(0.1, m))


def test_define_unit_validates_required_fields() -> None:
    with pytest.raises(UnitError):
        define_unit(name="", symbol="x", expr=m)

    with pytest.raises(UnitError):
        define_unit(name="x", symbol="", expr=m)


def test_define_unit_preserves_exact_fraction_scale() -> None:
    special = define_unit(
        name="special_length",
        symbol="sl",
        expr=Quantity(Fraction(3, 2), m),
    )

    assert special.scale == m.scale * Scale(Fraction(3, 2))
