"""Display resolution and formatting for the semantic core."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unitflow.core.quantities import Quantity
    from unitflow.core.units import Unit

from unitflow.core.scale import Scale


class DisplayResolver:
    """Resolves default display forms for units and quantities."""

    def __init__(self) -> None:
        self._derived_units: list[Unit] = []
        self._base_units: dict[str, Unit] = {}

    def register_base(self, dimension_name: str, unit: Unit) -> None:
        """Register a default base unit for a given dimension."""
        self._base_units[dimension_name] = unit

    def register_derived(self, unit: Unit) -> None:
        """Register a named derived unit for consideration."""
        self._derived_units.append(unit)

    def _matching_derived_units(self, unit: Unit) -> list[Unit]:
        return [
            candidate
            for candidate in self._derived_units
            if candidate.dimension == unit.dimension and candidate.scale == unit.scale
        ]

    def _preferred_display_unit(self, unit: Unit) -> Unit | None:
        matches = self._matching_derived_units(unit)
        if not matches:
            return None

        if unit.quantity_kind is not None:
            kind_matches = [candidate for candidate in matches if candidate.quantity_kind == unit.quantity_kind]
            if len(kind_matches) == 1:
                return kind_matches[0]

        generic_matches = [candidate for candidate in matches if candidate.quantity_kind is None]
        if len(generic_matches) == 1 and len(matches) == 1:
            return generic_matches[0]

        return None

    def _should_preserve_authored_unit(self, unit: Unit) -> bool:
        if unit.name:
            return True
        if not unit.symbol:
            return False
        return "*" not in unit.symbol and "/" not in unit.symbol

    def resolve(self, quantity: Quantity) -> Quantity:
        """Resolve a quantity to its cleanest known default display form."""
        unit = quantity.unit

        preferred = self._preferred_display_unit(unit)
        if preferred is not None:
            return quantity.to(preferred)

        if self._should_preserve_authored_unit(unit):
            return quantity
        return self._fallback_compound(quantity)

    def _fallback_compound(self, quantity: Quantity) -> Quantity:
        unit = quantity.unit
        mapping = unit.dimension.to_mapping()
        if not mapping:
            # Dimensionless fallback
            from unitflow.core.units import Unit
            return quantity.to(Unit.dimensionless(symbol=""))
        
        target_scale = Scale.one()
        numerator: list[tuple[str, int]] = []
        denominator: list[tuple[str, int]] = []
        
        # Sort dimensions for deterministic output (e.g. M L T ...)
        for dim_name, exp in mapping.items():
            base_u = self._base_units.get(dim_name)
            if not base_u:
                return quantity  # Cannot resolve compound, return as-is
            
            target_scale = target_scale * (base_u.scale ** exp)
            
            sym = base_u.symbol or base_u.name or dim_name
            if exp > 0:
                numerator.append((sym, exp))
            else:
                denominator.append((sym, -exp))
                
        symbol = self._build_symbol(numerator, denominator)
        
        from unitflow.core.units import Unit
        compound_unit = Unit(
            dimension=unit.dimension,
            scale=target_scale,
            symbol=symbol,
            quantity_kind=unit.quantity_kind,
        )
        return quantity.to(compound_unit)

    def resolve_unit_symbol(self, unit: Unit) -> str:
        """Resolve a unit to a display symbol string."""
        preferred = self._preferred_display_unit(unit)
        if preferred is not None and preferred.symbol:
            return preferred.symbol
        if self._should_preserve_authored_unit(unit):
            return unit.symbol or unit.name or ""
        return self._fallback_compound_symbol(unit)

    def _fallback_compound_symbol(self, unit: Unit) -> str:
        mapping = unit.dimension.to_mapping()
        if not mapping:
            return ""
        
        numerator: list[tuple[str, int]] = []
        denominator: list[tuple[str, int]] = []
        
        for dim_name, exp in mapping.items():
            base_u = self._base_units.get(dim_name)
            sym = dim_name
            if base_u:
                sym = base_u.symbol or base_u.name or dim_name
            
            if exp > 0:
                numerator.append((sym, exp))
            else:
                denominator.append((sym, -exp))
                
        return self._build_symbol(numerator, denominator)

    def _build_symbol(self, num: list[tuple[str, int]], den: list[tuple[str, int]]) -> str:
        def fmt(parts: list[tuple[str, int]]) -> str:
            res = []
            for sym, exp in parts:
                if exp == 1:
                    res.append(sym)
                else:
                    res.append(f"{sym}^{exp}")
            return " * ".join(res)
            
        num_str = fmt(num) or "1"
        if not den:
            return num_str
        
        den_str = fmt(den)
        if len(den) > 1:
            return f"{num_str} / ({den_str})"
        return f"{num_str} / {den_str}"


# TODO: Address global mutable state before serialization/distributed phases.
# The default resolver should likely become a context variable or be explicitly passed.
default_resolver = DisplayResolver()
