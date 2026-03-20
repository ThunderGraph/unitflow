from __future__ import annotations

import pytest

from unitflow import ANGLE, CYCLE_COUNT, SOLID_ANGLE, UnitFamily, UnitFamilyError


def test_predefined_families_have_stable_names() -> None:
    assert ANGLE.name == "angle"
    assert SOLID_ANGLE.name == "solid_angle"
    assert CYCLE_COUNT.name == "cycle_count"


def test_family_requires_non_empty_name() -> None:
    with pytest.raises(UnitFamilyError):
        UnitFamily(name="", description="bad")


def test_family_requires_non_empty_description() -> None:
    with pytest.raises(UnitFamilyError):
        UnitFamily(name="angle", description="")
