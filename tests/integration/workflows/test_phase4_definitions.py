from __future__ import annotations

import math

import pytest

from unitflow import Quantity, UnitNamespace, cm, ksi, lbf, m, mech, psi, rad, rpm, s


def test_phase4_acceptance_user_can_define_ksi_without_core_edits() -> None:
    materials = UnitNamespace("materials")
    custom_ksi = materials.define_unit(
        name="kilopound_per_square_inch_custom",
        symbol="ksi_custom",
        expr=1000 * psi,
    )

    assert custom_ksi == ksi


def test_phase4_acceptance_mixed_first_party_and_user_namespaces() -> None:
    custom = UnitNamespace("custom")
    custom_length = custom.define_unit(
        name="panel_width",
        symbol="panel_w",
        expr=Quantity(250, cm),
    )

    width = 2 * custom.panel_w

    assert width.to(m).magnitude == 5


def test_phase4_acceptance_mechanical_workflow() -> None:
    torque = 12 * (m * lbf)
    speed = 3000 * rpm
    angular_speed = speed.to(rad / s)
    power = torque * angular_speed

    assert angular_speed.magnitude == pytest.approx(100 * math.pi)
    assert power.unit.dimension.to_mapping() == {"length": 2, "mass": 1, "time": -3}


def test_phase4_acceptance_pressure_output_conversion() -> None:
    stress = 35 * ksi

    assert stress.to(psi).magnitude == 35000
