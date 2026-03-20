from __future__ import annotations

from fractions import Fraction
import math

import pytest

from unitflow import (
    DimensionMismatchError,
    Quantity,
    QuantityError,
)
from tests.helpers import make_centimeter, make_meter, make_minute, make_radian, make_second, make_turn


def make_meter_quantity(value: int | float | Fraction) -> Quantity:
    return Quantity(value, make_meter())


def test_quantity_requires_supported_magnitude_and_unit() -> None:
    with pytest.raises(QuantityError):
        Quantity(True, make_meter())  # type: ignore[arg-type]

    with pytest.raises(QuantityError):
        Quantity("3", make_meter())  # type: ignore[arg-type]

    with pytest.raises(QuantityError):
        Quantity(3, "meter")  # type: ignore[arg-type]


def test_quantity_to_converts_exactly_for_rational_scale() -> None:
    length = Quantity(3, make_meter())

    converted = length.to(make_centimeter())

    assert converted.magnitude == 300
    assert converted.unit == make_centimeter()


def test_quantity_add_and_subtract_with_compatible_units() -> None:
    meters = Quantity(3, make_meter())
    centimeters = Quantity(33, make_centimeter())

    assert meters + centimeters == Quantity(Fraction(333, 100), make_meter())
    assert meters - centimeters == Quantity(Fraction(267, 100), make_meter())


def test_quantity_add_and_subtract_incompatible_dimensions_raise() -> None:
    length = Quantity(3, make_meter())
    time = Quantity(2, make_second())

    with pytest.raises(DimensionMismatchError):
        _ = length + time

    with pytest.raises(DimensionMismatchError):
        _ = length - time


def test_quantity_multiply_divide_and_power() -> None:
    distance = Quantity(3, make_meter())
    width = Quantity(33, make_centimeter())
    duration = Quantity(2, make_second())

    area = distance * width
    velocity = distance / duration

    assert area.magnitude == 99
    assert area.unit.dimension.to_mapping() == {"length": 2}
    assert velocity.magnitude == Fraction(3, 2)
    assert velocity.unit.dimension.to_mapping() == {"length": 1, "time": -1}
    assert (distance**2).magnitude == 9


def test_quantity_reflected_scalar_multiplication_from_unit() -> None:
    quantity = 3 * make_meter()

    assert quantity == Quantity(3, make_meter())


def test_quantity_scalar_multiplication_and_division() -> None:
    quantity = 3 * make_meter()

    assert quantity * 2 == Quantity(6, make_meter())
    assert 2 * quantity == Quantity(6, make_meter())
    assert quantity / 2 == Quantity(Fraction(3, 2), make_meter())


def test_quantity_semantic_equality_and_hash_alignment() -> None:
    left = 3 * make_meter()
    right = 300 * make_centimeter()

    assert left == right
    assert hash(left) == hash(right)


def test_quantity_is_close_for_inexact_values() -> None:
    left = Quantity(0.99, make_meter() ** 2)
    right = 3 * make_meter() * 33 * make_centimeter()

    assert left.is_close(right)


def test_quantity_pi_bearing_conversion_works() -> None:
    rpm = Quantity(3000, make_turn() / make_minute())
    rad_per_second = rpm.to(make_radian() / make_second())

    assert rad_per_second.unit == make_radian() / make_second()
    assert rad_per_second.magnitude == pytest.approx(100 * math.pi)


def test_quantity_repr_is_readable_for_debugging() -> None:
    quantity = make_meter_quantity(3)

    assert repr(quantity) == "Quantity(magnitude=3, unit=Unit(dimension=Dimension(length=1), scale=Scale(1), name='meter', symbol='m'))"


def test_quantity_equality_returns_false_for_incompatible_units() -> None:
    assert (3 * make_meter()) != Quantity(3, make_second())


def test_quantity_equality_is_symmetric_for_exact_and_inexact_values() -> None:
    left = 3 * make_meter() * 33 * make_centimeter()
    right = Quantity(0.99, make_meter() ** 2)

    assert left == right
    assert right == left


def test_quantity_rtruediv_produces_inverse_unit_quantity() -> None:
    inverse = 5 / (3 * make_meter())

    assert inverse.magnitude == Fraction(5, 3)
    assert inverse.unit.dimension.to_mapping() == {"length": -1}
