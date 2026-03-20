"""Serialization for core semantic objects."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from unitflow.core.dimensions import Dimension
from unitflow.core.scale import Scale
from unitflow.core.unit_families import UnitFamily
from unitflow.core.units import Unit
from unitflow.core.quantities import Quantity
from unitflow.errors import SerializationError


def serialize_magnitude(magnitude: int | float | Fraction) -> dict[str, Any]:
    if isinstance(magnitude, int) and not isinstance(magnitude, bool):
        return {"type": "int", "value": magnitude}
    elif isinstance(magnitude, float):
        return {"type": "float", "value": magnitude}
    elif isinstance(magnitude, Fraction):
        return {
            "type": "fraction",
            "numerator": magnitude.numerator,
            "denominator": magnitude.denominator,
        }
    raise SerializationError(f"Unsupported magnitude type: {type(magnitude)}")


def deserialize_magnitude(data: dict[str, Any]) -> int | float | Fraction:
    try:
        mag_type = data["type"]
        if mag_type == "int":
            return int(data["value"])
        elif mag_type == "float":
            return float(data["value"])
        elif mag_type == "fraction":
            return Fraction(int(data["numerator"]), int(data["denominator"]))
        raise SerializationError(f"Unknown magnitude type: {mag_type}")
    except KeyError as exc:
        raise SerializationError(f"Missing key in magnitude data: {exc}") from exc


def serialize_dimension(dimension: Dimension) -> dict[str, Any]:
    return {"exponents": list(dimension.exponents)}


def deserialize_dimension(data: dict[str, Any]) -> Dimension:
    try:
        return Dimension(tuple(data["exponents"]))
    except (KeyError, TypeError) as exc:
        raise SerializationError(f"Invalid dimension data: {exc}") from exc


def serialize_scale(scale: Scale) -> dict[str, Any]:
    return {
        "coefficient": {
            "numerator": scale.coefficient.numerator,
            "denominator": scale.coefficient.denominator,
        },
        "pi_power": scale.pi_power,
    }


def deserialize_scale(data: dict[str, Any]) -> Scale:
    try:
        coeff_data = data["coefficient"]
        return Scale.from_ratio(
            coeff_data["numerator"],
            coeff_data["denominator"],
            pi_power=data["pi_power"],
        )
    except (KeyError, TypeError) as exc:
        raise SerializationError(f"Invalid scale data: {exc}") from exc


def serialize_unit_family(family: UnitFamily) -> dict[str, Any]:
    return {
        "name": family.name,
        "description": family.description,
    }


def deserialize_unit_family(data: dict[str, Any]) -> UnitFamily:
    try:
        return UnitFamily(name=data["name"], description=data["description"])
    except KeyError as exc:
        raise SerializationError(f"Missing key in unit family data: {exc}") from exc


def serialize_unit(unit: Unit) -> dict[str, Any]:
    return {
        "dimension": serialize_dimension(unit.dimension),
        "scale": serialize_scale(unit.scale),
        "name": unit.name,
        "symbol": unit.symbol,
        "aliases": list(unit.aliases),
        "family": serialize_unit_family(unit.family) if unit.family else None,
        "quantity_kind": unit.quantity_kind,
    }


def deserialize_unit(data: dict[str, Any]) -> Unit:
    try:
        return Unit(
            dimension=deserialize_dimension(data["dimension"]),
            scale=deserialize_scale(data["scale"]),
            name=data.get("name"),
            symbol=data.get("symbol"),
            aliases=tuple(data.get("aliases", [])),
            family=deserialize_unit_family(data["family"]) if data.get("family") else None,
            quantity_kind=data.get("quantity_kind"),
        )
    except KeyError as exc:
        raise SerializationError(f"Missing key in unit data: {exc}") from exc


def serialize_quantity(quantity: Quantity) -> dict[str, Any]:
    return {
        "magnitude": serialize_magnitude(quantity.magnitude),
        "unit": serialize_unit(quantity.unit),
    }


def deserialize_quantity(data: dict[str, Any]) -> Quantity:
    try:
        return Quantity(
            magnitude=deserialize_magnitude(data["magnitude"]),
            unit=deserialize_unit(data["unit"]),
        )
    except KeyError as exc:
        raise SerializationError(f"Missing key in quantity data: {exc}") from exc
