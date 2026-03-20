from __future__ import annotations

from unitflow import ANGLE, Dimension, Scale, Unit


def make_meter() -> Unit:
    return Unit(
        dimension=Dimension.base("length"),
        scale=Scale.one(),
        name="meter",
        symbol="m",
    )


def make_centimeter() -> Unit:
    return Unit(
        dimension=Dimension.base("length"),
        scale=Scale.from_ratio(1, 100),
        name="centimeter",
        symbol="cm",
    )


def make_second() -> Unit:
    return Unit(
        dimension=Dimension.base("time"),
        scale=Scale.one(),
        name="second",
        symbol="s",
    )


def make_minute() -> Unit:
    return Unit(
        dimension=Dimension.base("time"),
        scale=Scale.from_int(60),
        name="minute",
        symbol="min",
    )


def make_radian() -> Unit:
    return Unit.dimensionless(name="radian", symbol="rad", family=ANGLE)


def make_turn() -> Unit:
    return Unit(
        dimension=Dimension.zero(),
        scale=Scale.from_int(2) * Scale.pi(),
        name="turn",
        symbol="turn",
        family=ANGLE,
    )
