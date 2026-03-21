"""SI prefix generation for scalable unit catalogs."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from unitflow.core.quantities import Quantity
from unitflow.core.units import Unit
from unitflow.define.namespaces import UnitNamespace

if TYPE_CHECKING:
    from unitflow.core.display import DisplayResolver

SI_PREFIXES: dict[str, tuple[str, Fraction]] = {
    "pico":  ("p",  Fraction(1, 1_000_000_000_000)),
    "nano":  ("n",  Fraction(1, 1_000_000_000)),
    "micro": ("u",  Fraction(1, 1_000_000)),
    "milli": ("m",  Fraction(1, 1_000)),
    "centi": ("c",  Fraction(1, 100)),
    "deci":  ("d",  Fraction(1, 10)),
    "deca":  ("da", Fraction(10, 1)),
    "hecto": ("h",  Fraction(100, 1)),
    "kilo":  ("k",  Fraction(1_000, 1)),
    "mega":  ("M",  Fraction(1_000_000, 1)),
    "giga":  ("G",  Fraction(1_000_000_000, 1)),
    "tera":  ("T",  Fraction(1_000_000_000_000, 1)),
}


def generate_prefixes(
    namespace: UnitNamespace,
    base_unit: Unit,
    *,
    prefixes: dict[str, tuple[str, Fraction]] | None = None,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
    resolver: DisplayResolver | None = None,
) -> dict[str, Unit]:
    """Generate prefixed variants of a base unit and register them in a namespace.

    Returns a dict mapping prefix names to the created units.
    """
    if prefixes is None:
        prefixes = SI_PREFIXES

    if base_unit.name is None or base_unit.symbol is None:
        from unitflow.errors import UnitError
        raise UnitError("Base unit must have both a name and symbol to generate prefixes.")

    generated: dict[str, Unit] = {}

    for prefix_name, (prefix_symbol, factor) in prefixes.items():
        if include is not None and prefix_name not in include:
            continue
        if exclude is not None and prefix_name in exclude:
            continue

        new_name = f"{prefix_name}{base_unit.name}"
        new_symbol = f"{prefix_symbol}{base_unit.symbol}"

        new_unit = namespace.define_unit(
            name=new_name,
            symbol=new_symbol,
            expr=Quantity(factor, base_unit),
            quantity_kind=base_unit.quantity_kind,
        )

        if resolver is not None:
            resolver.register_derived(new_unit)

        generated[prefix_name] = new_unit

    return generated
