from __future__ import annotations

from unitflow import N, Quantity, m, si


def test_phase5_acceptance_torque_defaults_to_Nm_with_semantic_hints() -> None:
    # `m * N` has dimension L^2 M T^-2
    # Without quantity_kind, it's ambiguous because J and torque_unit both match.
    # By providing `quantity_kind="torque"`, it should resolve to N*m.
    torque_unit = N * m
    torque = Quantity(12, torque_unit.with_metadata(quantity_kind="torque"))

    assert str(torque) == "12 N*m"


def test_phase5_acceptance_energy_displays_as_J_when_unambiguous_or_hinted() -> None:
    energy_unit = N * m
    energy = Quantity(12, energy_unit.with_metadata(quantity_kind="energy"))

    assert str(energy) == "12 J"


def test_phase5_acceptance_machinist_output_forces_final_units() -> None:
    # A multi-step calculation might end up in some intermediate unit
    area = 3 * si.m * 33 * si.cm

    # We force the final unit explicitly
    machinist_output = area.to(si.mm**2)

    assert str(machinist_output) == "990000 mm^2"


def test_phase5_acceptance_compound_fallback_avoiding_mixed_authored_units() -> None:
    area = 3 * si.m * 33 * si.cm

    # Evaluated area is 99 in `m * cm`
    # Default display resolver should see L^2 and fall back to building `m^2`, which scales it
    assert str(area) == "0.99 m^2"
