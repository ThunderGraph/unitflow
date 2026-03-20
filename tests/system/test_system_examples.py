"""
Unitflow System Examples
========================

End-to-end demonstrations that exercise the full library stack:
core algebra, catalogs, display, symbolic constraints, serialization, and NumPy.

Run with: uv run pytest examples/test_system_examples.py -v
"""

from __future__ import annotations

import json
import math

import pytest

from unitflow import (
    Conjunction,
    DimensionMismatchError,
    Equation,
    Hz,
    IncompatibleUnitError,
    J,
    N,
    Pa,
    Quantity,
    Unit,
    UnitNamespace,
    W,
    cm,
    define_unit,
    deserialize_constraint,
    deserialize_quantity,
    kg,
    ksi,
    m,
    mm,
    psi,
    rad,
    rpm,
    s,
    serialize_constraint,
    serialize_quantity,
    symbol,
)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. BASIC ENGINEERING CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════


class TestBasicEngineeringCalculations:
    """Prove the library handles everyday engineering math cleanly."""

    def test_force_equals_mass_times_acceleration(self) -> None:
        mass = 2 * kg
        accel = 9.81 * (m / s**2)
        force = mass * accel

        assert force.to(N).is_close(Quantity(19.62, N))

    def test_pressure_from_force_and_area(self) -> None:
        force = 500 * N
        area = Quantity(2, m**2)
        pressure = force / area

        assert pressure.to(Pa) == Quantity(250, Pa)

    def test_kinetic_energy(self) -> None:
        mass = 10 * kg
        velocity = 3 * (m / s)
        ke = Quantity(1, Unit.dimensionless()) / 2 * mass * velocity**2

        assert ke.to(J).is_close(Quantity(45.0, J))

    def test_power_from_energy_and_time(self) -> None:
        energy = 1000 * J
        time = 10 * s
        power = energy / time

        assert power == Quantity(100, W)

    def test_frequency_conversion(self) -> None:
        freq = 60 * Hz
        period = 1 / freq

        assert period.is_close(Quantity(1 / 60, s))


# ═══════════════════════════════════════════════════════════════════════════════
# 2. UNIT CONVERSION WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════════


class TestUnitConversionWorkflows:
    """Prove conversions work across SI and mechanical engineering units."""

    def test_length_conversions(self) -> None:
        length = 1 * m

        assert length.to(cm) == Quantity(100, cm)
        assert length.to(mm) == Quantity(1000, mm)

    def test_rpm_to_rad_per_second(self) -> None:
        speed = 3000 * rpm
        angular = speed.to(rad / s)

        assert angular.is_close(Quantity(100 * math.pi, rad / s))

    def test_pressure_unit_conversion_for_machinist(self) -> None:
        stress = 35 * ksi

        in_psi = stress.to(psi)
        assert in_psi.magnitude == 35000

    def test_mixed_unit_area_normalizes_cleanly(self) -> None:
        width = 3 * m
        depth = 50 * cm
        area = width * depth

        area_m2 = area.to(m**2)
        assert area_m2.is_close(Quantity(1.5, m**2))

    def test_semantic_equality_across_units(self) -> None:
        a = 1 * m
        b = 100 * cm

        assert a == b
        assert hash(a) == hash(b)

        quantities = {a, b}
        assert len(quantities) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DISPLAY AND FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════


class TestDisplayAndFormatting:
    """Prove the display layer produces engineering-friendly output."""

    def test_named_unit_display(self) -> None:
        force = 10 * N
        assert str(force) == "10 N"

    def test_compound_unit_display(self) -> None:
        velocity = 10 * (m / s)
        assert "m" in str(velocity)
        assert "s" in str(velocity)

    def test_explicit_output_unit_overrides_default(self) -> None:
        area = 3 * m * 50 * cm
        machinist_output = area.to(mm**2)

        output_str = str(machinist_output)
        assert "mm^2" in output_str

    def test_torque_vs_energy_disambiguation(self) -> None:
        torque_unit = (N * m).with_metadata(quantity_kind="torque")
        torque = Quantity(12, torque_unit)
        assert str(torque) == "12 N*m"

        energy_unit = (N * m).with_metadata(quantity_kind="energy")
        energy = Quantity(12, energy_unit)
        assert str(energy) == "12 J"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. USER-DEFINED UNITS AND EXTENSIBILITY
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtensibility:
    """Prove users can define their own units without touching core code."""

    def test_define_custom_unit(self) -> None:
        from fractions import Fraction

        ft = define_unit(
            name="foot",
            symbol="ft",
            expr=Quantity(Fraction(3048, 10000), m),
        )

        height = 6 * ft
        height_m = height.to(m)
        assert height_m.is_close(Quantity(1.8288, m))

    def test_custom_namespace(self) -> None:
        aero = UnitNamespace("aero")
        aero.define_unit(
            name="knot",
            symbol="kn",
            expr=Quantity(1852, m / s),
        )

        speed = 250 * aero.kn
        speed_ms = speed.to(m / s)

        assert speed_ms.is_close(Quantity(250 * 1852, m / s))

    def test_derived_unit_from_existing_catalog(self) -> None:
        materials = UnitNamespace("materials")
        custom_ksi = materials.define_unit(
            name="custom_ksi",
            symbol="ksi_custom",
            expr=1000 * psi,
        )

        assert custom_ksi == ksi


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SYMBOLIC CONSTRAINTS (MBSE / ThunderGraph)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSymbolicConstraints:
    """Prove the symbolic expression and constraint layer works for MBSE."""

    def test_equation_authoring(self) -> None:
        force = symbol("F", unit=N)
        mass = symbol("m", unit=kg)
        accel = symbol("a", unit=m / s**2)

        constraint = force == mass * accel

        assert isinstance(constraint, Equation)

    def test_bounded_variable(self) -> None:
        x = symbol("x", unit=m)
        bounds = (0 * m <= x) & (x <= 10 * m)

        assert isinstance(bounds, Conjunction)

    def test_quantity_symbol_dispatch_symmetry(self) -> None:
        force = symbol("F", unit=N)

        eq1 = force == 5 * N
        eq2 = force == 5 * N

        assert isinstance(eq1, Equation)
        assert isinstance(eq2, Equation)
        assert eq1.is_same(eq2)

    def test_constraint_negation(self) -> None:
        x = symbol("x", unit=m)
        c = x <= 10 * m
        negated = ~c

        from unitflow import StrictInequality

        assert isinstance(negated, StrictInequality)
        assert negated.operator == ">"

    def test_model_oriented_example(self) -> None:
        shaft_speed = symbol("shaft_speed", unit=rpm)
        shaft_torque = symbol("shaft_torque", unit=N * m, quantity_kind="torque")
        shaft_power = symbol("shaft_power", unit=W)

        shaft_omega = shaft_speed.to(rad / s)
        power_balance = shaft_power == shaft_torque * shaft_omega
        speed_bounds = (0 * rpm <= shaft_speed) & (shaft_speed <= 6000 * rpm)

        assert isinstance(power_balance, Equation)
        assert isinstance(speed_bounds, Conjunction)

    def test_boolean_coercion_trap(self) -> None:
        x = symbol("x", unit=m)
        c = x == 5 * m

        from unitflow import BooleanCoercionError

        with pytest.raises(BooleanCoercionError):
            if c:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SERIALIZATION ROUND-TRIPS
# ═══════════════════════════════════════════════════════════════════════════════


class TestSerialization:
    """Prove quantities and constraints survive serialization."""

    def test_quantity_json_round_trip(self) -> None:
        q = 3000 * rpm

        data = serialize_quantity(q)
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        restored = deserialize_quantity(loaded)

        assert restored == q
        assert restored.unit.symbol == "rpm"

    def test_constraint_tree_round_trip(self) -> None:
        x = symbol("x", unit=m)
        constraint = ((0 * m) <= x) & (x <= 10 * m)

        data = serialize_constraint(constraint)
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        restored = deserialize_constraint(loaded)

        assert restored.is_same(constraint)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. NUMPY ARRAY WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════════

np = pytest.importorskip("numpy")
from numpy.testing import assert_array_almost_equal  # noqa: E402


class TestNumPyWorkflows:
    """Prove array-backed engineering computation works."""

    def test_vectorized_force_calculation(self) -> None:
        masses = Quantity(np.array([1.0, 2.0, 5.0, 10.0]), kg)
        accel = Quantity(np.array([9.81, 9.81, 9.81, 9.81]), m / s**2)

        forces = masses * accel

        assert forces.unit == kg * m / s**2
        assert_array_almost_equal(forces.magnitude, [9.81, 19.62, 49.05, 98.1])

    def test_array_unit_conversion(self) -> None:
        lengths = Quantity(np.array([1.0, 2.5, 0.3]), m)
        in_cm = lengths.to(cm)

        assert_array_almost_equal(in_cm.magnitude, [100.0, 250.0, 30.0])

    def test_array_reductions_preserve_units(self) -> None:
        distances = Quantity(np.array([10.0, 20.0, 30.0]), m)

        total = np.sum(distances)
        average = np.mean(distances)

        assert total.unit == m
        assert total.magnitude == 60.0
        assert average.unit == m
        assert average.magnitude == 20.0

    def test_trig_on_dimensionless_arrays(self) -> None:
        angles = Quantity(np.array([0, np.pi / 2, np.pi]), rad)
        sines = np.sin(angles)

        assert sines.unit.dimension.is_dimensionless
        assert_array_almost_equal(sines.magnitude, [0.0, 1.0, 0.0])

    def test_trig_rejects_dimensional_arrays(self) -> None:
        lengths = Quantity(np.array([1.0, 2.0]), m)

        with pytest.raises(DimensionMismatchError):
            np.sin(lengths)

    def test_scalar_and_array_produce_same_units(self) -> None:
        scalar_force = (2 * kg) * (9.81 * (m / s**2))
        array_force = Quantity(np.array([2.0]), kg) * Quantity(np.array([9.81]), m / s**2)

        assert scalar_force.unit == array_force.unit


# ═══════════════════════════════════════════════════════════════════════════════
# 8. ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Prove the library fails cleanly and helpfully."""

    def test_dimension_mismatch_on_addition(self) -> None:
        with pytest.raises(DimensionMismatchError):
            _ = (3 * m) + (2 * s)

    def test_incompatible_conversion(self) -> None:
        with pytest.raises(IncompatibleUnitError):
            (3 * m).to(s)

    def test_unary_negation(self) -> None:
        q = 5 * m
        neg = -q
        assert neg.magnitude == -5
        assert neg.unit == m
