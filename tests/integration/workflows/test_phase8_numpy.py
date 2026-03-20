from __future__ import annotations

import pytest

pytest.importorskip("numpy")

import numpy as np

from unitflow import DimensionMismatchError, Quantity
from unitflow.catalogs.si import kg, m, rad, s


def test_phase8_acceptance_scalar_and_array_quantity_arithmetic_follow_same_rules() -> None:
    # Scalar workflow
    mass_scalar = Quantity(2, kg)
    accel_scalar = Quantity(9.81, m / s**2)
    force_scalar = mass_scalar * accel_scalar

    # Array workflow
    mass_array = Quantity(np.array([2, 4]), kg)
    accel_array = Quantity(np.array([9.81, 9.81]), m / s**2)
    force_array = mass_array * accel_array

    assert force_scalar.unit == force_array.unit
    assert force_array.magnitude.tolist() == [19.62, 39.24]


def test_phase8_acceptance_trigonometric_numpy_operations_reject_invalid_inputs() -> None:
    # Valid: angles are essentially dimensionless at the base
    angles = Quantity(np.array([0, np.pi/2, np.pi]), rad)
    sines = np.sin(angles)
    assert sines.unit == rad

    # Invalid: lengths have dimension L
    lengths = Quantity(np.array([1, 2, 3]), m)

    with pytest.raises(DimensionMismatchError):
        _ = np.sin(lengths)
