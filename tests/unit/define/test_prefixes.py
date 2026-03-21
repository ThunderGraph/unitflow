"""Unit tests for prefix generation."""

from fractions import Fraction

import pytest

from unitflow import Dimension, Quantity, Scale, Unit, UnitError
from unitflow.core.display import DisplayResolver
from unitflow.define.namespaces import UnitNamespace
from unitflow.define.prefixes import generate_prefixes


def test_generate_prefixes_basic() -> None:
    ns = UnitNamespace("test")
    m = ns.register(
        Unit(
            dimension=Dimension.base("length"),
            scale=Scale.one(),
            name="meter",
            symbol="m",
        )
    )

    prefixes = generate_prefixes(ns, m, include={"kilo", "milli"})

    assert "kilo" in prefixes
    assert "milli" in prefixes
    assert len(prefixes) == 2

    km = prefixes["kilo"]
    assert km.name == "kilometer"
    assert km.symbol == "km"
    assert km.scale == Scale.from_int(1000)

    mm = prefixes["milli"]
    assert mm.name == "millimeter"
    assert mm.symbol == "mm"
    assert mm.scale == Scale.from_ratio(1, 1000)

def test_generate_prefixes_requires_name_and_symbol() -> None:
    ns = UnitNamespace("test")
    m = Unit(dimension=Dimension.base("length"), scale=Scale.one())

    with pytest.raises(UnitError, match="must have both a name and symbol"):
        generate_prefixes(ns, m, include={"kilo"})

def test_generate_prefixes_with_custom_prefixes() -> None:
    ns = UnitNamespace("test")
    m = ns.register(
        Unit(
            dimension=Dimension.base("length"),
            scale=Scale.one(),
            name="meter",
            symbol="m",
        )
    )

    custom_prefixes = {
        "mega": ("M", Fraction(10**6)),
        "micro": ("u", Fraction(1, 10**6)),
    }

    prefixes = generate_prefixes(ns, m, prefixes=custom_prefixes)

    assert "mega" in prefixes
    assert "micro" in prefixes
    assert prefixes["mega"].symbol == "Mm"
    assert prefixes["micro"].symbol == "um"

def test_generate_prefixes_with_resolver() -> None:
    ns = UnitNamespace("test")
    m = ns.register(
        Unit(
            dimension=Dimension.base("length"),
            scale=Scale.one(),
            name="meter",
            symbol="m",
        )
    )

    resolver = DisplayResolver()
    prefixes = generate_prefixes(ns, m, include={"kilo"}, resolver=resolver)

    km = prefixes["kilo"]
    # Check if registered by seeing if resolve gives it back when requested
    q = Quantity(1, km)
    resolved = resolver.resolve(q)
    assert resolved.unit == km

def test_generate_prefixes_exclude() -> None:
    ns = UnitNamespace("test")
    m = ns.register(
        Unit(
            dimension=Dimension.base("length"),
            scale=Scale.one(),
            name="meter",
            symbol="m",
        )
    )

    # exclude "kilo" from all SI_PREFIXES
    prefixes = generate_prefixes(ns, m, exclude={"kilo"})
    assert "kilo" not in prefixes
    assert "milli" in prefixes
    assert "mega" in prefixes
