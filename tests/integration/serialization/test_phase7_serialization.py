from __future__ import annotations

import pytest

from unitflow import Quantity
from unitflow.catalogs.si import m, s, kg, N
from unitflow.catalogs.mechanical import rpm
from unitflow.expr.symbols import symbol
from unitflow.serialization.quantities import serialize_quantity, deserialize_quantity
from unitflow.serialization.expressions import serialize_constraint, deserialize_constraint

def test_phase7_acceptance_quantity_serialization_preserves_canonical_identity_and_metadata() -> None:
    q = Quantity(3000, rpm.with_metadata(quantity_kind="angular_velocity"))
    
    data = serialize_quantity(q)
    restored = deserialize_quantity(data)
    
    assert restored == q
    assert restored.unit.symbol == "rpm"
    assert restored.unit.quantity_kind == "angular_velocity"
    assert restored.magnitude == 3000

def test_phase7_acceptance_constraint_tree_round_trips_without_losing_logical_structure() -> None:
    x = symbol("x", unit=m)
    constraint = ((0 * m) <= x) & (x <= 10 * m)
    
    data = serialize_constraint(constraint)
    restored = deserialize_constraint(data)
    
    assert restored.is_same(constraint)
