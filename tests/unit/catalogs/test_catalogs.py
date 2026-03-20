from __future__ import annotations

from fractions import Fraction

from unitflow import Hz, J, N, Pa, Unit, W, cm, inch, kg, lbf, m, mech, psi, rad, rpm, s, si


def test_si_catalog_exposes_expected_units() -> None:
    assert si.m == m
    assert si.cm == cm
    assert si.kg == kg
    assert si.N == N
    assert si.Pa == Pa
    assert si.J == J
    assert si.W == W
    assert si.Hz == Hz
    assert si.resolve("metre") == m


def test_mechanical_catalog_exposes_expected_units() -> None:
    assert mech.rpm == rpm
    assert mech.lbf == lbf
    assert mech.psi == psi


def test_derived_si_units_are_semantically_correct() -> None:
    assert kg * m / (s**2) == N
    assert Pa == N / (m**2)
    assert N * m == J
    assert J / s == W
    assert Hz == Unit.dimensionless() / s


def test_mechanical_units_are_semantically_correct() -> None:
    assert rpm.conversion_factor_to(rad / s).coefficient == Fraction(1, 30)
    assert rpm.conversion_factor_to(rad / s).pi_power == 1
    assert psi == lbf / (inch**2)
