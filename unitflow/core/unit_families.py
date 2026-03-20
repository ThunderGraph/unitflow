"""Unit-family metadata primitives for pseudo-dimensionless units."""

from __future__ import annotations

from dataclasses import dataclass

from unitflow.errors import UnitFamilyError


@dataclass(frozen=True, slots=True)
class UnitFamily:
    """Semantic metadata for units that share a meaningful family."""

    name: str
    description: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise UnitFamilyError("Unit family names must be non-empty.")
        if not self.description or not self.description.strip():
            raise UnitFamilyError("Unit family descriptions must be non-empty.")


ANGLE = UnitFamily(
    name="angle",
    description="Angular units such as radian and turn.",
)

SOLID_ANGLE = UnitFamily(
    name="solid_angle",
    description="Solid-angle units such as steradian.",
)

CYCLE_COUNT = UnitFamily(
    name="cycle_count",
    description="Cycle-based counting units such as cycle and revolution.",
)
