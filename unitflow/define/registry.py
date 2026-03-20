"""Registry primitives for composing multiple unit namespaces."""

from __future__ import annotations

from unitflow.core.units import Unit
from unitflow.define.namespaces import UnitNamespace
from unitflow.errors import UnitError


class UnitRegistry:
    """A lightweight registry that resolves identifiers across namespaces."""

    def __init__(self, name: str = "registry"):
        if not isinstance(name, str) or not name.strip():
            raise UnitError("UnitRegistry requires a non-empty name.")
        self.name = name
        self._namespaces: dict[str, UnitNamespace] = {}

    def add_namespace(self, namespace: UnitNamespace) -> UnitNamespace:
        if not isinstance(namespace, UnitNamespace):
            raise UnitError("UnitRegistry.add_namespace() expects a UnitNamespace.")
        existing = self._namespaces.get(namespace.name)
        if existing is not None and existing is not namespace:
            raise UnitError(
                f"Namespace '{namespace.name}' is already registered in registry '{self.name}'."
            )
        self._namespaces[namespace.name] = namespace
        return namespace

    def resolve(self, identifier: str) -> Unit:
        matches: list[Unit] = []
        for namespace in self._namespaces.values():
            if identifier in namespace:
                matches.append(namespace.resolve(identifier))
        if not matches:
            raise UnitError(
                f"Unknown identifier '{identifier}' in registry '{self.name}'."
            )
        first = matches[0]
        if any(match != first for match in matches[1:]):
            raise UnitError(
                f"Identifier '{identifier}' is ambiguous across namespaces in registry '{self.name}'."
            )
        return first

    def namespaces(self) -> tuple[str, ...]:
        return tuple(sorted(self._namespaces))
