"""First-party SI starter catalog."""

from __future__ import annotations

from unitflow.core.dimensions import Dimension
from unitflow.core.display import default_resolver
from unitflow.core.scale import Scale
from unitflow.core.unit_families import ANGLE
from unitflow.core.units import Unit
from unitflow.define.namespaces import UnitNamespace
from unitflow.define.prefixes import generate_prefixes

si = UnitNamespace("si")

m = si.register(
    Unit(
        dimension=Dimension.base("length"),
        scale=Scale.one(),
        name="meter",
        symbol="m",
        aliases=("metre",),
    )
)
cm = si.register(
    Unit(
        dimension=Dimension.base("length"),
        scale=Scale.from_ratio(1, 100),
        name="centimeter",
        symbol="cm",
    )
)
mm = si.register(
    Unit(
        dimension=Dimension.base("length"),
        scale=Scale.from_ratio(1, 1000),
        name="millimeter",
        symbol="mm",
    )
)
s = si.register(
    Unit(
        dimension=Dimension.base("time"),
        scale=Scale.one(),
        name="second",
        symbol="s",
    )
)
minute = si.register(
    Unit(
        dimension=Dimension.base("time"),
        scale=Scale.from_int(60),
        name="minute",
        symbol="min",
    )
)
kg = si.register(
    Unit(
        dimension=Dimension.base("mass"),
        scale=Scale.one(),
        name="kilogram",
        symbol="kg",
    )
)
A = si.register(
    Unit(
        dimension=Dimension.base("current"),
        scale=Scale.one(),
        name="ampere",
        symbol="A",
    )
)
rad = si.register(
    Unit.dimensionless(
        name="radian",
        symbol="rad",
        family=ANGLE,
    )
)
turn = si.register(
    Unit(
        dimension=Dimension.zero(),
        scale=Scale.from_int(2) * Scale.pi(),
        name="turn",
        symbol="turn",
        aliases=("revolution", "rev"),
        family=ANGLE,
    )
)

N = si.define_unit(name="newton", symbol="N", expr=kg * m / (s**2))
Pa = si.define_unit(name="pascal", symbol="Pa", expr=N / (m**2))
J = si.define_unit(name="joule", symbol="J", expr=N * m, quantity_kind="energy")
W = si.define_unit(name="watt", symbol="W", expr=J / s, quantity_kind="power")
Hz = si.define_unit(name="hertz", symbol="Hz", expr=Unit.dimensionless() / s, quantity_kind="frequency")

# Register bases for formatting
default_resolver.register_base("length", m)
default_resolver.register_base("mass", kg)
default_resolver.register_base("time", s)
default_resolver.register_base("current", A)

# Register derived units for clean display matching
default_resolver.register_derived(N)
default_resolver.register_derived(Pa)
default_resolver.register_derived(J)
default_resolver.register_derived(W)
default_resolver.register_derived(Hz)

# Explicitly register a torque display preference to avoid collapsing to Joules
torque_unit = si.define_unit(name="newton_meter", symbol="N*m", expr=N * m, quantity_kind="torque")
default_resolver.register_derived(torque_unit)

# ─── Generate SI prefix variants ────────────────────────────────────────────

_common_prefixes = {"milli", "micro", "nano", "kilo", "mega", "giga"}

_W_prefixes = generate_prefixes(si, W, include=_common_prefixes, resolver=default_resolver)
_N_prefixes = generate_prefixes(si, N, include=_common_prefixes, resolver=default_resolver)
_Pa_prefixes = generate_prefixes(si, Pa, include=_common_prefixes, resolver=default_resolver)
_J_prefixes = generate_prefixes(si, J, include=_common_prefixes, resolver=default_resolver)
_Hz_prefixes = generate_prefixes(si, Hz, include=_common_prefixes, resolver=default_resolver)
_m_prefixes = generate_prefixes(si, m, include={"micro", "nano", "kilo"}, resolver=default_resolver)
_s_prefixes = generate_prefixes(si, s, include={"milli", "micro", "nano"}, resolver=default_resolver)

# Convenience module-level aliases for the most commonly used prefixed units
kW = _W_prefixes["kilo"]
MW = _W_prefixes["mega"]
GW = _W_prefixes["giga"]
mW = _W_prefixes["milli"]

kN = _N_prefixes["kilo"]
MN = _N_prefixes["mega"]
mN = _N_prefixes["milli"]

kPa = _Pa_prefixes["kilo"]
MPa = _Pa_prefixes["mega"]
GPa = _Pa_prefixes["giga"]

kJ = _J_prefixes["kilo"]
MJ = _J_prefixes["mega"]
GJ = _J_prefixes["giga"]

kHz = _Hz_prefixes["kilo"]
MHz = _Hz_prefixes["mega"]
GHz = _Hz_prefixes["giga"]

km = _m_prefixes["kilo"]
um = _m_prefixes["micro"]
nm = _m_prefixes["nano"]

ms = _s_prefixes["milli"]
us = _s_prefixes["micro"]
ns = _s_prefixes["nano"]
