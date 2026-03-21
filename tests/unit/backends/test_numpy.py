"""Tests for NumPy backend integration."""

from __future__ import annotations

import pytest

pytest.importorskip("numpy")

import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal

from unitflow import DimensionMismatchError, Quantity, Scale, Unit
from unitflow.catalogs.si import m, rad, s


def test_numpy_array_as_magnitude_is_supported() -> None:
    arr = np.array([1, 2, 3])
    q = Quantity(arr, m)

    assert isinstance(q.magnitude, np.ndarray)
    assert_array_equal(q.magnitude, arr)
    assert q.unit == m


def test_numpy_multiplication_preserves_semantics() -> None:
    q1 = Quantity(np.array([1, 2, 3]), m)
    q2 = Quantity(np.array([4, 5, 6]), s)

    # Quantity * Quantity
    res = q1 * q2
    assert res.unit == m * s
    assert_array_equal(res.magnitude, np.array([4, 10, 18]))

    # Quantity * scalar
    res_scalar = q1 * 2
    assert res_scalar.unit == m
    assert_array_equal(res_scalar.magnitude, np.array([2, 4, 6]))

    # Numpy multiplication dispatch
    res_np = np.multiply(q1, q2)
    assert res_np.unit == m * s
    assert_array_equal(res_np.magnitude, np.array([4, 10, 18]))


def test_numpy_addition_converts_units() -> None:
    q1 = Quantity(np.array([1, 2, 3]), m)

    # essentially cm
    cm_unit = Unit(dimension=m.dimension, scale=m.scale * Scale.from_ratio(1, 100))
    q2 = Quantity(np.array([100, 200, 300]), cm_unit)

    res = np.add(q1, q2)
    assert res.unit == m
    assert_array_almost_equal(res.magnitude, np.array([2.0, 4.0, 6.0]))


def test_numpy_addition_rejects_dimension_mismatch() -> None:
    q1 = Quantity(np.array([1, 2]), m)
    q2 = Quantity(np.array([1, 2]), s)

    with pytest.raises(DimensionMismatchError):
        np.add(q1, q2)


def test_numpy_transcendental_functions_demand_dimensionless() -> None:
    angles = Quantity(np.array([np.pi / 2, np.pi]), rad)

    res = np.sin(angles)
    assert res.unit.dimension.is_dimensionless
    assert_array_almost_equal(res.magnitude, np.array([1.0, 0.0]))

    lengths = Quantity(np.array([1, 2]), m)
    with pytest.raises(DimensionMismatchError):
        np.sin(lengths)


def test_numpy_reductions() -> None:
    q = Quantity(np.array([1.0, 2.0, 3.0]), m)

    res_sum = np.sum(q)
    assert res_sum.unit == m
    assert res_sum.magnitude == 6.0

    res_mean = np.mean(q)
    assert res_mean.unit == m
    assert res_mean.magnitude == 2.0

def test_numpy_other_reductions() -> None:
    q = Quantity(np.array([1.0, 2.0, 3.0]), m)

    assert np.min(q).magnitude == 1.0
    assert np.min(q).unit == m

    assert np.max(q).magnitude == 3.0
    assert np.max(q).unit == m

    assert np.median(q).magnitude == 2.0
    assert np.median(q).unit == m

def test_numpy_reductions_with_kwargs() -> None:
    q = Quantity(np.array([1.0, 2.0, 3.0]), m)
    initial = Quantity(10.0, m)
    res = np.sum(q, initial=initial)
    assert res.magnitude == 16.0
    assert res.unit == m

    # testing where
    res_where = np.sum(q, where=np.array([True, False, True]))
    assert res_where.magnitude == 4.0
    assert res_where.unit == m

def test_numpy_transcendental_functions_other() -> None:
    q = Quantity(np.array([0, np.pi/4]), rad)
    assert_array_almost_equal(np.cos(q).magnitude, [1.0, np.sqrt(2)/2])
    assert_array_almost_equal(np.tan(q).magnitude, [0.0, 1.0])

    q2 = Quantity(np.array([1, 2]), Unit.dimensionless())
    assert_array_almost_equal(np.exp(q2).magnitude, [np.e, np.e**2])
    assert_array_almost_equal(np.log(q2).magnitude, [0.0, np.log(2)])
    assert_array_almost_equal(np.log10(q2).magnitude, [0.0, np.log10(2)])
    assert_array_almost_equal(np.log2(q2).magnitude, [0.0, 1.0])

def test_numpy_subtract() -> None:
    q1 = Quantity(np.array([3, 4]), m)
    q2 = Quantity(np.array([1, 2]), m)

    res = np.subtract(q1, q2)
    assert res.unit == m
    assert_array_equal(res.magnitude, np.array([2, 2]))

def test_numpy_power_and_sqrt() -> None:
    q = Quantity(np.array([4, 9]), m)

    res_sq = np.square(q)
    assert res_sq.unit == m**2
    assert_array_equal(res_sq.magnitude, np.array([16, 81]))

    res_pow = np.power(q, 3)
    assert res_pow.unit == m**3
    assert_array_equal(res_pow.magnitude, np.array([64, 729]))

def test_numpy_divide() -> None:
    q1 = Quantity(np.array([4, 6]), m)

    # array quantity / scalar
    res = np.divide(q1, 2)
    assert res.unit == m
    assert_array_equal(res.magnitude, np.array([2, 3]))

def test_numpy_out_parameter() -> None:
    q1 = Quantity(np.array([1, 2]), m)
    q2 = Quantity(np.array([3, 4]), m)

    out_arr = np.zeros(2)
    res = np.add(q1, q2, out=out_arr)

    # When out is passed, the array is returned, not a quantity
    assert isinstance(res, np.ndarray)
    assert_array_equal(res, np.array([4, 6]))
    assert_array_equal(out_arr, np.array([4, 6]))
