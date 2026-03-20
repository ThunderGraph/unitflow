from __future__ import annotations

from fractions import Fraction

import pytest

from unitflow import (
    ANGLE,
    Dimension,
    IncompatibleUnitError,
    Scale,
    Unit,
    UnitError,
)
from tests.helpers import make_centimeter, make_meter, make_minute, make_radian, make_second, make_turn


def test_unit_requires_dimension_and_scale_types() -> None:
    with pytest.raises(UnitError):
        Unit(dimension="length", scale=Scale.one())  # type: ignore[arg-type]

    with pytest.raises(UnitError):
        Unit(dimension=Dimension.base("length"), scale="1")  # type: ignore[arg-type]


def test_unit_validates_metadata_fields() -> None:
    with pytest.raises(UnitError):
        Unit(dimension=Dimension.base("length"), scale=Scale.one(), name=" ")

    with pytest.raises(UnitError):
        Unit(dimension=Dimension.base("length"), scale=Scale.one(), symbol=" ")

    with pytest.raises(UnitError):
        Unit(
            dimension=Dimension.base("length"),
            scale=Scale.one(),
            aliases=("valid", ""),
        )


def test_unit_multiply_divide_and_power() -> None:
    meter = make_meter()
    second = make_second()

    area = meter * meter
    velocity = meter / second
    acceleration = velocity / second

    assert area.dimension.to_mapping() == {"length": 2}
    assert velocity.dimension.to_mapping() == {"length": 1, "time": -1}
    assert acceleration.dimension.to_mapping() == {"length": 1, "time": -2}
    assert (meter**2).dimension.to_mapping() == {"length": 2}


def test_unit_compatibility_and_exact_conversion_factor() -> None:
    meter = make_meter()
    centimeter = make_centimeter()

    assert meter.is_compatible_with(centimeter)
    assert meter.conversion_factor_to(centimeter) == Scale.from_int(100)
    assert centimeter.conversion_factor_to(meter) == Scale.from_ratio(1, 100)


def test_incompatible_conversion_factor_raises() -> None:
    meter = make_meter()
    second = make_second()

    with pytest.raises(IncompatibleUnitError):
        meter.conversion_factor_to(second)


def test_semantically_equivalent_units_compare_and_hash_identically() -> None:
    kilogram = Unit(
        dimension=Dimension.base("mass"),
        scale=Scale.one(),
        name="kilogram",
        symbol="kg",
    )
    meter = make_meter()
    second = make_second()
    newton_named = Unit(
        dimension=Dimension.from_mapping({"length": 1, "mass": 1, "time": -2}),
        scale=Scale.one(),
        name="newton",
        symbol="N",
    )
    newton_composite = kilogram * meter / (second**2)

    assert newton_named == newton_composite
    assert hash(newton_named) == hash(newton_composite)


def test_manually_constructed_area_units_have_area_semantics() -> None:
    meter = make_meter()
    centimeter = make_centimeter()

    area_unit = meter * centimeter

    assert area_unit.dimension.to_mapping() == {"length": 2}
    assert area_unit.scale == Scale.from_ratio(1, 100)


def test_manually_constructed_rpm_equivalent_derives_exact_conversion_factor() -> None:
    rpm_equivalent = make_turn() / make_minute()
    rad_per_second = make_radian() / make_second()

    factor = rpm_equivalent.conversion_factor_to(rad_per_second)

    assert factor.coefficient == Fraction(1, 30)
    assert factor.pi_power == 1


def test_unit_repr_is_readable_for_debugging() -> None:
    meter = make_meter()

    assert repr(meter) == "Unit(dimension=Dimension(length=1), scale=Scale(1), name='meter', symbol='m')"


def test_unit_dimensionless_constructor_preserves_family_metadata() -> None:
    radian = make_radian()

    assert radian.dimension.is_dimensionless
    assert radian.family == ANGLE


def test_with_metadata_returns_updated_copy() -> None:
    meter = make_meter()

    renamed = meter.with_metadata(
        name="metre",
        symbol="metre",
        aliases=("meter", "metre"),
        family=make_radian().family,
    )

    assert renamed is not meter
    assert renamed.dimension == meter.dimension
    assert renamed.scale == meter.scale
    assert renamed.name == "metre"
    assert renamed.symbol == "metre"
    assert renamed.aliases == ("meter", "metre")
    assert renamed.family == make_radian().family
    assert meter.name == "meter"
    assert meter.symbol == "m"


def test_quantity_kind_does_not_change_semantic_equality_or_hashing() -> None:
    energy_like = (make_meter() ** 2 / (make_second() ** 2)).with_metadata(quantity_kind="energy")
    torque_like = (make_meter() ** 2 / (make_second() ** 2)).with_metadata(quantity_kind="torque")

    assert energy_like == torque_like
    assert hash(energy_like) == hash(torque_like)


def test_with_metadata_can_set_quantity_kind() -> None:
    meter = make_meter()
    typed = meter.with_metadata(quantity_kind="length")

    assert typed.quantity_kind == "length"
