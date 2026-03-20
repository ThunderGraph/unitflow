"""Namespace primitives for unit catalogs and user-defined packs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from unitflow.core.unit_families import UnitFamily
from unitflow.core.units import Unit
from unitflow.define.define_unit import define_unit
from unitflow.errors import UnitError

if TYPE_CHECKING:
    from unitflow.core.quantities import Quantity


def _iter_identifiers(unit: Unit) -> tuple[str, ...]:
    identifiers: list[str] = []
    for candidate in (unit.symbol, unit.name, *unit.aliases):
        if candidate and candidate not in identifiers:
            identifiers.append(candidate)
    return tuple(identifiers)


class UnitNamespace:
    """A simple named namespace for unit lookup by symbol, name, or alias."""

    def __init__(self, name: str):
        if not isinstance(name, str) or not name.strip():
            raise UnitError("UnitNamespace requires a non-empty name.")
        self.name = name
        self._units: dict[str, Unit] = {}

    def register(self, unit: Unit) -> Unit:
        if not isinstance(unit, Unit):
            raise UnitError("UnitNamespace.register() expects a Unit.")
        for identifier in _iter_identifiers(unit):
            existing = self._units.get(identifier)
            if existing is not None and existing != unit:
                raise UnitError(
                    f"Identifier '{identifier}' is already registered in namespace '{self.name}'."
                )
            self._units[identifier] = unit
        return unit

    def define_unit(
        self,
        *,
        name: str,
        symbol: str,
        expr: Unit | Quantity,
        aliases: tuple[str, ...] = (),
        family: UnitFamily | None = None,
        quantity_kind: str | None = None,
    ) -> Unit:
        unit = define_unit(
            name=name,
            symbol=symbol,
            expr=expr,
            aliases=aliases,
            family=family,
            quantity_kind=quantity_kind,
        )
        return self.register(unit)

    def resolve(self, identifier: str) -> Unit:
        try:
            return self._units[identifier]
        except KeyError as exc:
            raise UnitError(
                f"Unknown identifier '{identifier}' in namespace '{self.name}'."
            ) from exc

    def __getstate__(self) -> dict:
        return self.__dict__

    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)

    def __getattr__(self, name: str) -> Unit:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._units[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __contains__(self, identifier: object) -> bool:
        return isinstance(identifier, str) and identifier in self._units

    def identifiers(self) -> tuple[str, ...]:
        return tuple(sorted(self._units))
