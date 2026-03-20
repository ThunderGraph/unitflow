from __future__ import annotations

from unitflow import Dimension, Quantity, Scale, Unit
from unitflow.core.display import DisplayResolver


def test_display_resolver_keeps_authored_symbol() -> None:
    resolver = DisplayResolver()
    meter = Unit(
        dimension=Dimension.base("length"),
        scale=Scale.one(),
        symbol="m",
    )

    q = Quantity(3, meter)
    resolved = resolver.resolve(q)

    assert resolved is q
    assert resolved.unit.symbol == "m"


def test_display_resolver_prefers_unambiguous_derived_unit() -> None:
    resolver = DisplayResolver()
    m = Unit(dimension=Dimension.base("length"), scale=Scale.one(), symbol="m")
    s = Unit(dimension=Dimension.base("time"), scale=Scale.one(), symbol="s")
    kg = Unit(dimension=Dimension.base("mass"), scale=Scale.one(), symbol="kg")

    N = Unit(
        dimension=m.dimension * kg.dimension / (s.dimension**2),
        scale=Scale.one(),
        symbol="N",
    )
    resolver.register_derived(N)

    # Construct a nameless composite unit matching Newton
    nameless = kg * m / (s**2)
    q = Quantity(5, nameless)

    resolved = resolver.resolve(q)

    assert resolved.unit == N
    assert resolved.unit.symbol == "N"
    assert resolved.magnitude == 5


def test_display_resolver_matches_quantity_kind() -> None:
    resolver = DisplayResolver()
    m = Unit(dimension=Dimension.base("length"), scale=Scale.one(), symbol="m")
    kg = Unit(dimension=Dimension.base("mass"), scale=Scale.one(), symbol="kg")
    s = Unit(dimension=Dimension.base("time"), scale=Scale.one(), symbol="s")

    nameless_energy = kg * (m**2) / (s**2)

    J = Unit(dimension=nameless_energy.dimension, scale=Scale.one(), symbol="J", quantity_kind="energy")
    Nm = Unit(dimension=nameless_energy.dimension, scale=Scale.one(), symbol="N*m", quantity_kind="torque")

    resolver.register_derived(J)
    resolver.register_derived(Nm)

    # Has energy kind, should resolve to J
    q_energy = Quantity(5, nameless_energy.with_metadata(quantity_kind="energy"))
    resolved_energy = resolver.resolve(q_energy)
    assert resolved_energy.unit == J

    # Has torque kind, should resolve to N*m
    q_torque = Quantity(5, nameless_energy.with_metadata(quantity_kind="torque"))
    resolved_torque = resolver.resolve(q_torque)
    assert resolved_torque.unit == Nm


def test_display_resolver_falls_back_to_compound_when_ambiguous() -> None:
    resolver = DisplayResolver()
    m = Unit(dimension=Dimension.base("length"), scale=Scale.one(), symbol="m")
    kg = Unit(dimension=Dimension.base("mass"), scale=Scale.one(), symbol="kg")
    s = Unit(dimension=Dimension.base("time"), scale=Scale.one(), symbol="s")

    resolver.register_base("length", m)
    resolver.register_base("mass", kg)
    resolver.register_base("time", s)

    nameless = kg * (m**2) / (s**2)

    # Register both J and N*m without differentiating the query
    J = Unit(dimension=nameless.dimension, scale=Scale.one(), symbol="J", quantity_kind="energy")
    Nm = Unit(dimension=nameless.dimension, scale=Scale.one(), symbol="N*m", quantity_kind="torque")
    resolver.register_derived(J)
    resolver.register_derived(Nm)

    # Query with no quantity_kind -> ambiguous
    q = Quantity(5, nameless)
    resolved = resolver.resolve(q)

    # Should not be J or Nm, should be the compound unit built from bases
    assert resolved.unit.symbol == "m^2 * kg / s^2" or resolved.unit.symbol == "kg * m^2 / s^2" # Depending on dict order
    # Test just string building logic basically, checking it has symbols
    assert "m^2" in resolved.unit.symbol
    assert "kg" in resolved.unit.symbol
    assert "s^2" in resolved.unit.symbol
