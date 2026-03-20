from __future__ import annotations

import math
import pytest
from fractions import Fraction

from unitflow import Scale, ScaleError


def test_exact_scale_composition_for_common_units() -> None:
    centimeter = Scale.from_ratio(1, 100)
    minute = Scale.from_int(60)
    turn = Scale.from_int(2) * Scale.pi()

    assert centimeter.coefficient == Fraction(1, 100)
    assert minute.coefficient == Fraction(60, 1)
    assert turn.coefficient == Fraction(2, 1)
    assert turn.pi_power == 1


def test_scale_cancellation_with_pi() -> None:
    rpm = (Scale.from_int(2) * Scale.pi()) / Scale.from_int(60)
    angular_period_factor = Scale.from_int(60) / (Scale.from_int(2) * Scale.pi())

    assert rpm * angular_period_factor == Scale.one()


def test_scale_power_and_inverse() -> None:
    scale = Scale.from_ratio(3, 2, pi_power=1)

    assert scale**2 == Scale(Fraction(9, 4), 2)
    assert scale / scale == Scale.one()


def test_scale_zero_denominator_raises() -> None:
    with pytest.raises(ScaleError):
        Scale.from_ratio(1, 0)


def test_scale_zero_negative_power_raises() -> None:
    with pytest.raises(ScaleError):
        Scale.zero() ** -1


def test_scale_zero_with_pi_power_raises() -> None:
    with pytest.raises(ScaleError):
        Scale.from_ratio(0, 1, pi_power=1)


def test_scale_rejects_float_coefficients() -> None:
    with pytest.raises(ScaleError):
        Scale(0.1, 0)


def test_equivalent_scales_are_equal_and_hash_identically() -> None:
    a = Scale.from_ratio(1, 100)
    b = Scale(Fraction(1, 100), 0)

    assert a == b
    assert hash(a) == hash(b)


def test_scale_repr_is_readable() -> None:
    assert repr(Scale.from_ratio(3, 2, pi_power=1)) == "Scale(3/2 * pi^1)"


def test_scale_as_float_is_lossy_but_predictable() -> None:
    half_pi = Scale.from_ratio(1, 2, pi_power=1)

    assert half_pi.as_float() == pytest.approx(math.pi / 2)
