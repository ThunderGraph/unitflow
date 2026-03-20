from __future__ import annotations

import subprocess
import sys

from unitflow import ANGLE, Dimension, Scale


def test_importing_semantic_core_does_not_import_numpy() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import unitflow; print('numpy' in sys.modules)",
        ],
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.stdout.strip() == "False"


def test_turn_can_be_represented_exactly() -> None:
    radian_dimension = Dimension.zero()
    turn_scale = Scale.from_int(2) * Scale.pi()

    assert radian_dimension.is_dimensionless
    assert turn_scale.coefficient.numerator == 2
    assert turn_scale.coefficient.denominator == 1
    assert turn_scale.pi_power == 1


def test_rpm_prerequisites_do_not_require_eighth_dimension() -> None:
    angle_dimension = Dimension.zero()
    time_dimension = Dimension.base("time")
    turn_scale = Scale.from_int(2) * Scale.pi()
    minute_scale = Scale.from_int(60)

    rpm_dimension = angle_dimension / time_dimension
    rpm_scale = turn_scale / minute_scale

    assert rpm_dimension.to_mapping() == {"time": -1}
    assert rpm_scale.coefficient.numerator == 1
    assert rpm_scale.coefficient.denominator == 30
    assert rpm_scale.pi_power == 1


def test_unit_family_metadata_is_preserved_in_semantic_prerequisites() -> None:
    prepared_turn = {
        "dimension": Dimension.zero(),
        "scale": Scale.from_int(2) * Scale.pi(),
        "family": ANGLE,
    }

    assert prepared_turn["dimension"].is_dimensionless
    assert prepared_turn["family"] == ANGLE
    assert prepared_turn["family"].name == "angle"
