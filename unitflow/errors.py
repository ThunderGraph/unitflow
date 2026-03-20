"""Shared exception hierarchy for unitflow."""


class UnitflowError(Exception):
    """Base exception for all unitflow-specific errors."""


class SemanticCoreError(UnitflowError):
    """Raised for invalid operations in the semantic core."""


class DimensionError(SemanticCoreError):
    """Raised when dimension construction or algebra is invalid."""


class ScaleError(SemanticCoreError):
    """Raised when exact scale construction or algebra is invalid."""


class UnitFamilyError(SemanticCoreError):
    """Raised when unit-family metadata is invalid."""


class UnitError(SemanticCoreError):
    """Raised when unit construction or unit algebra is invalid."""


class IncompatibleUnitError(UnitError):
    """Raised when unit compatibility is required but not satisfied."""


class QuantityError(SemanticCoreError):
    """Raised when quantity construction or quantity arithmetic is invalid."""


class DimensionMismatchError(QuantityError):
    """Raised when quantity arithmetic requires compatible dimensions and they do not match."""


class SerializationError(UnitflowError):
    """Raised when serialization or deserialization fails."""
