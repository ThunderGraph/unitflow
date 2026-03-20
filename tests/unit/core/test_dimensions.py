from __future__ import annotations

import pytest

from unitflow import Dimension, DimensionError


def test_zero_dimension_is_dimensionless() -> None:
    dimension = Dimension.zero()

    assert dimension.is_dimensionless
    assert dimension.to_mapping() == {}


def test_base_dimension_by_name() -> None:
    length = Dimension.base("length")

    assert length.to_mapping() == {"length": 1}


def test_dimension_multiply_divide_and_power() -> None:
    length = Dimension.base("length")
    time = Dimension.base("time")

    velocity = length / time
    area = length * length

    assert velocity.to_mapping() == {"length": 1, "time": -1}
    assert area.to_mapping() == {"length": 2}
    assert (velocity**2).to_mapping() == {"length": 2, "time": -2}


def test_dimension_from_mapping_validates_names() -> None:
    with pytest.raises(DimensionError):
        Dimension.from_mapping({"velocity": 1})


def test_dimension_from_mapping_validates_types() -> None:
    with pytest.raises(DimensionError):
        Dimension.from_mapping({"length": 1.5})  # type: ignore[arg-type]


def test_dimension_requires_full_base_length() -> None:
    with pytest.raises(DimensionError):
        Dimension((1, 0, 0))


def test_equivalent_dimensions_are_equal_and_hash_identically() -> None:
    force_a = Dimension.from_mapping({"length": 1, "mass": 1, "time": -2})
    force_b = Dimension.base("mass") * Dimension.base("length") / (Dimension.base("time") ** 2)

    assert force_a == force_b
    assert hash(force_a) == hash(force_b)


def test_direct_dimension_constructor_validates_exponent_types() -> None:
    with pytest.raises(DimensionError):
        Dimension((1.0, 0, 0, 0, 0, 0, 0))  # type: ignore[arg-type]


def test_dimension_repr_is_readable() -> None:
    force = Dimension.from_mapping({"length": 1, "mass": 1, "time": -2})

    assert repr(force) == "Dimension(length=1, mass=1, time=-2)"
