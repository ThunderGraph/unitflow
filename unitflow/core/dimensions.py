"""Dimension algebra for the unitflow semantic core."""

from __future__ import annotations

from dataclasses import dataclass

from unitflow.errors import DimensionError

BASE_DIMENSION_NAMES = (
    "length",
    "mass",
    "time",
    "current",
    "temperature",
    "amount",
    "luminous_intensity",
)
_BASE_INDEX = {name: index for index, name in enumerate(BASE_DIMENSION_NAMES)}


@dataclass(frozen=True, slots=True)
class Dimension:
    """Immutable exponent vector over the fixed base-dimension basis."""

    exponents: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.exponents) != len(BASE_DIMENSION_NAMES):
            raise DimensionError(
                f"Expected {len(BASE_DIMENSION_NAMES)} exponents, got {len(self.exponents)}."
            )
        for exponent in self.exponents:
            if not isinstance(exponent, int):
                raise DimensionError("Dimension exponents must be integers.")

    @classmethod
    def zero(cls) -> Dimension:
        """Return the dimensionless exponent vector."""

        return cls((0,) * len(BASE_DIMENSION_NAMES))

    @classmethod
    def base(cls, name: str) -> Dimension:
        """Return a single base dimension by its canonical name."""

        try:
            index = _BASE_INDEX[name]
        except KeyError as exc:
            valid = ", ".join(BASE_DIMENSION_NAMES)
            raise DimensionError(f"Unknown base dimension '{name}'. Valid names: {valid}.") from exc

        exponents = [0] * len(BASE_DIMENSION_NAMES)
        exponents[index] = 1
        return cls(tuple(exponents))

    @classmethod
    def from_mapping(cls, exponents_by_name: dict[str, int]) -> Dimension:
        """Construct a dimension vector from a sparse base-dimension mapping."""

        exponents = [0] * len(BASE_DIMENSION_NAMES)
        for name, exponent in exponents_by_name.items():
            if not isinstance(exponent, int):
                raise DimensionError("Mapped dimension exponents must be integers.")
            try:
                index = _BASE_INDEX[name]
            except KeyError as exc:
                valid = ", ".join(BASE_DIMENSION_NAMES)
                raise DimensionError(
                    f"Unknown base dimension '{name}'. Valid names: {valid}."
                ) from exc
            exponents[index] = exponent
        return cls(tuple(exponents))

    @property
    def is_dimensionless(self) -> bool:
        """Whether all exponents are zero."""

        return all(exponent == 0 for exponent in self.exponents)

    def to_mapping(self) -> dict[str, int]:
        """Return a sparse mapping of non-zero exponents by base-dimension name."""

        return {
            name: exponent
            for name, exponent in zip(BASE_DIMENSION_NAMES, self.exponents, strict=True)
            if exponent != 0
        }

    def __mul__(self, other: Dimension) -> Dimension:
        if not isinstance(other, Dimension):
            return NotImplemented
        return Dimension(
            tuple(
                left + right
                for left, right in zip(self.exponents, other.exponents, strict=True)
            )
        )

    def __truediv__(self, other: Dimension) -> Dimension:
        if not isinstance(other, Dimension):
            return NotImplemented
        return Dimension(
            tuple(
                left - right
                for left, right in zip(self.exponents, other.exponents, strict=True)
            )
        )

    def __pow__(self, power: int) -> Dimension:
        if not isinstance(power, int):
            raise DimensionError("Dimensions can only be raised to integer powers.")
        return Dimension(tuple(exponent * power for exponent in self.exponents))

    def __repr__(self) -> str:
        if self.is_dimensionless:
            return "Dimension()"
        mapping = ", ".join(
            f"{name}={exponent}" for name, exponent in self.to_mapping().items()
        )
        return f"Dimension({mapping})"
