from __future__ import annotations

from fractions import Fraction

from unitflow import Dimension, Scale, Unit
from tests.helpers import make_centimeter, make_meter, make_minute, make_radian, make_second, make_turn


def test_manual_meter_and_centimeter_yield_area_semantics() -> None:
    meter = make_meter()
    centimeter = make_centimeter()

    area_unit = meter * centimeter

    assert area_unit.dimension.to_mapping() == {"length": 2}
    assert area_unit.scale == Scale.from_ratio(1, 100)


def test_manual_rpm_equivalent_derives_exact_rad_per_second_factor() -> None:
    turn = make_turn()
    minute = make_minute()
    radian = make_radian()
    second = make_second()

    rpm_equivalent = turn / minute
    rad_per_second = radian / second
    factor = rpm_equivalent.conversion_factor_to(rad_per_second)

    assert factor.coefficient == Fraction(1, 30)
    assert factor.pi_power == 1


def test_named_and_composite_force_units_are_semantically_equivalent() -> None:
    kilogram = Unit(
        dimension=Dimension.base("mass"),
        scale=Scale.one(),
        name="kilogram",
        symbol="kg",
    )
    meter = make_meter()
    second = make_second()
    newton = Unit(
        dimension=Dimension.from_mapping({"length": 1, "mass": 1, "time": -2}),
        scale=Scale.one(),
        name="newton",
        symbol="N",
    )

    composite = kilogram * meter / (second**2)

    assert composite == newton
