from __future__ import annotations

import math

import pytest

from unitflow import DimensionMismatchError, Quantity
from tests.helpers import make_centimeter, make_meter, make_minute, make_radian, make_second, make_turn


def test_phase3_acceptance_addition_and_dimension_mismatch() -> None:
    meters = 3 * make_meter()
    centimeters = 33 * make_centimeter()

    assert (meters + centimeters).is_close(Quantity(3.33, make_meter()))

    with pytest.raises(DimensionMismatchError):
        _ = meters + (2 * make_second())


def test_phase3_acceptance_area_semantics() -> None:
    area = 3 * make_meter() * 33 * make_centimeter()

    assert area == Quantity(0.99, make_meter() ** 2)


def test_phase3_acceptance_rpm_conversion() -> None:
    rpm = Quantity(3000, make_turn() / make_minute())
    angular_speed = rpm.to(make_radian() / make_second())

    assert angular_speed.magnitude == pytest.approx(100 * math.pi)


def test_phase3_acceptance_semantic_hash_behavior() -> None:
    quantities = {3 * make_meter(), 300 * make_centimeter()}

    assert len(quantities) == 1
