"""Unit semantics for the unitflow semantic core."""

from __future__ import annotations

from dataclasses import dataclass

from unitflow.core.dimensions import Dimension
from unitflow.core.scale import Scale
from unitflow.core.unit_families import UnitFamily
from unitflow.errors import IncompatibleUnitError, UnitError


_UNSET = object()

@dataclass(frozen=True, slots=True, eq=False)
class Unit:
    """Immutable semantic unit definition."""

    dimension: Dimension
    scale: Scale
    name: str | None = None
    symbol: str | None = None
    aliases: tuple[str, ...] = ()
    family: UnitFamily | None = None
    quantity_kind: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.dimension, Dimension):
            raise UnitError("Unit.dimension must be a Dimension.")
        if not isinstance(self.scale, Scale):
            raise UnitError("Unit.scale must be a Scale.")
        if self.name is not None and not self.name.strip():
            raise UnitError("Unit.name must be non-empty when provided.")
        if self.symbol is not None and not self.symbol.strip():
            raise UnitError("Unit.symbol must be non-empty when provided.")
        aliases = tuple(self.aliases)
        for alias in aliases:
            if not isinstance(alias, str) or not alias.strip():
                raise UnitError("Unit.aliases must contain only non-empty strings.")
        object.__setattr__(self, "aliases", aliases)

    @classmethod
    def dimensionless(
        cls,
        *,
        name: str | None = None,
        symbol: str | None = None,
        aliases: tuple[str, ...] = (),
        family: UnitFamily | None = None,
        quantity_kind: str | None = None,
    ) -> Unit:
        return cls(
            dimension=Dimension.zero(),
            scale=Scale.one(),
            name=name,
            symbol=symbol,
            aliases=aliases,
            family=family,
            quantity_kind=quantity_kind,
        )

    def is_compatible_with(self, other: Unit) -> bool:
        if not isinstance(other, Unit):
            return False
        return self.dimension == other.dimension

    def conversion_factor_to(self, other: Unit) -> Scale:
        if not isinstance(other, Unit):
            raise UnitError("Can only compute conversion factors between Unit instances.")
        if not self.is_compatible_with(other):
            raise IncompatibleUnitError(
                f"Incompatible units: {self!r} cannot convert to {other!r}."
            )
        return self.scale / other.scale

    def with_metadata(
        self,
        *,
        name: str | None | object = _UNSET,
        symbol: str | None | object = _UNSET,
        aliases: tuple[str, ...] | None | object = _UNSET,
        family: UnitFamily | None | object = _UNSET,
        quantity_kind: str | None | object = _UNSET,
    ) -> Unit:
        return Unit(
            dimension=self.dimension,
            scale=self.scale,
            name=self.name if name is _UNSET else name,  # type: ignore[arg-type]
            symbol=self.symbol if symbol is _UNSET else symbol,  # type: ignore[arg-type]
            aliases=self.aliases if aliases is _UNSET else aliases,  # type: ignore[arg-type]
            family=self.family if family is _UNSET else family,  # type: ignore[arg-type]
            quantity_kind=self.quantity_kind if quantity_kind is _UNSET else quantity_kind,  # type: ignore[arg-type]
        )

    def __mul__(self, other: Unit) -> Unit:
        if not isinstance(other, Unit):
            return NotImplemented
        new_symbol = None
        if self.symbol and other.symbol:
            new_symbol = f"{self.symbol}*{other.symbol}"
        return Unit(
            dimension=self.dimension * other.dimension,
            scale=self.scale * other.scale,
            symbol=new_symbol,
        )

    def __rmul__(self, other: object):
        from unitflow.core.quantities import Quantity, is_supported_magnitude

        if is_supported_magnitude(other):
            return Quantity(other, self, _explicit_display=True)
        return NotImplemented

    def __truediv__(self, other: Unit) -> Unit:
        if not isinstance(other, Unit):
            return NotImplemented
        new_symbol = None
        if self.symbol and other.symbol:
            new_symbol = f"{self.symbol}/{other.symbol}"
        return Unit(
            dimension=self.dimension / other.dimension,
            scale=self.scale / other.scale,
            symbol=new_symbol,
        )

    def __pow__(self, power: int) -> Unit:
        if not isinstance(power, int):
            raise UnitError("Units can only be raised to integer powers.")
        new_symbol = None
        if self.symbol:
            new_symbol = f"{self.symbol}^{power}"
        return Unit(
            dimension=self.dimension**power,
            scale=self.scale**power,
            symbol=new_symbol,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Unit):
            return NotImplemented
        return self.dimension == other.dimension and self.scale == other.scale

    def __hash__(self) -> int:
        return hash((self.dimension, self.scale))

    def __repr__(self) -> str:
        parts: list[str] = [f"dimension={self.dimension!r}", f"scale={self.scale!r}"]
        if self.name is not None:
            parts.append(f"name={self.name!r}")
        if self.symbol is not None:
            parts.append(f"symbol={self.symbol!r}")
        if self.aliases:
            parts.append(f"aliases={self.aliases!r}")
        if self.family is not None:
            parts.append(f"family={self.family.name!r}")
        if self.quantity_kind is not None:
            parts.append(f"quantity_kind={self.quantity_kind!r}")
        return f"Unit({', '.join(parts)})"

    def __str__(self) -> str:
        if self.symbol:
            return self.symbol
        if self.name:
            return self.name
        
        from unitflow.core.display import default_resolver
        return default_resolver.resolve_unit_symbol(self)

