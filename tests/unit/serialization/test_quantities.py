from __future__ import annotations

import pytest
from fractions import Fraction
import json

from unitflow.core.dimensions import Dimension
from unitflow.core.scale import Scale
from unitflow.core.unit_families import ANGLE
from unitflow.core.units import Unit
from unitflow.core.quantities import Quantity
from unitflow.errors import SerializationError
from unitflow.serialization.quantities import (
    serialize_dimension,
    deserialize_dimension,
    serialize_scale,
    deserialize_scale,
    serialize_unit,
    deserialize_unit,
    serialize_quantity,
    deserialize_quantity,
)
from unitflow.catalogs.si import m


def test_dimension_serialization_roundtrip() -> None:
    dim = Dimension.base("length") * Dimension.base("time") ** -2
    data = serialize_dimension(dim)
    restored = deserialize_dimension(data)
    assert restored == dim


def test_scale_serialization_roundtrip() -> None:
    scale = Scale.from_ratio(3, 2, pi_power=1)
    data = serialize_scale(scale)
    restored = deserialize_scale(data)
    assert restored == scale


def test_unit_serialization_roundtrip() -> None:
    # Use a unit with all fields
    u = Unit(
        dimension=m.dimension,
        scale=m.scale * Scale.from_int(2),
        name="double_meter",
        symbol="2m",
        aliases=("dm",),
        family=ANGLE,
        quantity_kind="length_kind"
    )
    data = serialize_unit(u)
    restored = deserialize_unit(data)
    
    assert restored == u
    assert restored.name == u.name
    assert restored.symbol == u.symbol
    assert restored.aliases == u.aliases
    assert restored.family == u.family
    assert restored.quantity_kind == u.quantity_kind


def test_quantity_serialization_roundtrip_int() -> None:
    q = Quantity(5, m)
    data = serialize_quantity(q)
    restored = deserialize_quantity(data)
    assert restored == q
    assert type(restored.magnitude) is int


def test_quantity_serialization_roundtrip_float() -> None:
    q = Quantity(5.5, m)
    data = serialize_quantity(q)
    restored = deserialize_quantity(data)
    assert restored == q
    assert type(restored.magnitude) is float


def test_quantity_serialization_roundtrip_fraction() -> None:
    q = Quantity(Fraction(1, 3), m)
    data = serialize_quantity(q)
    restored = deserialize_quantity(data)
    assert restored == q
    assert type(restored.magnitude) is Fraction


def test_serialization_error_on_invalid_data() -> None:
    with pytest.raises(SerializationError):
        deserialize_dimension({"wrong": 1})
        
    with pytest.raises(SerializationError):
        deserialize_scale({"wrong": 1})


def test_quantity_serialization_is_json_safe() -> None:
    q = Quantity(Fraction(1, 3), m)
    data = serialize_quantity(q)
    
    # Must dump/load cleanly
    json_str = json.dumps(data)
    loaded_data = json.loads(json_str)
    
    restored = deserialize_quantity(loaded_data)
    assert restored == q
