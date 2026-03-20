from __future__ import annotations

import pytest

from unitflow import Quantity, UnitError, UnitNamespace, UnitRegistry, cm, define_unit, m


def test_namespace_resolves_symbol_name_and_alias() -> None:
    namespace = UnitNamespace("custom")
    meter = define_unit(name="meter", symbol="m", expr=m, aliases=("metre",))
    namespace.register(meter)

    assert namespace.m == meter
    assert namespace.meter == meter
    assert namespace.metre == meter
    assert namespace.resolve("metre") == meter


def test_namespace_rejects_identifier_collisions() -> None:
    namespace = UnitNamespace("custom")
    namespace.register(define_unit(name="meter", symbol="m", expr=m))

    with pytest.raises(UnitError):
        namespace.register(define_unit(name="centimeter_conflict", symbol="m", expr=cm))


def test_registry_resolves_across_namespaces() -> None:
    left = UnitNamespace("left")
    right = UnitNamespace("right")
    left.register(define_unit(name="meter_left", symbol="ml", expr=m))
    right.register(define_unit(name="meter_right", symbol="mr", expr=m))

    registry = UnitRegistry("main")
    registry.add_namespace(left)
    registry.add_namespace(right)

    assert registry.resolve("ml") == left.ml
    assert registry.resolve("mr") == right.mr


def test_registry_rejects_ambiguous_identifiers() -> None:
    left = UnitNamespace("left")
    right = UnitNamespace("right")
    left.register(define_unit(name="meter_left", symbol="m_common", expr=m))
    right.register(
        define_unit(
            name="centimeter_right",
            symbol="m_common",
            expr=Quantity(1, cm),
        )
    )

    registry = UnitRegistry("main")
    registry.add_namespace(left)
    registry.add_namespace(right)

    with pytest.raises(UnitError):
        registry.resolve("m_common")
