"""Tests for NumPy backend integration."""

from __future__ import annotations

import pytest

pytest.importorskip("numpy")

import numpy as np
from numpy.testing import assert_array_equal, assert_array_almost_equal

from unitflow import Quantity, DimensionMismatchError, Unit, Scale
from unitflow.catalogs.si import m, s, kg, rad
from unitflow.catalogs.mechanical import rpm


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
