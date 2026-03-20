"""First-party mechanical starter catalog."""

from __future__ import annotations

from fractions import Fraction

from unitflow.core.quantities import Quantity
from unitflow.core.dimensions import Dimension
from unitflow.core.scale import Scale
from unitflow.core.units import Unit
from unitflow.catalogs.si import N, minute, turn
from unitflow.define.namespaces import UnitNamespace

mech = UnitNamespace("mech")

inch = mech.register(
    Unit(
        dimension=Dimension.base("length"),
        scale=Scale(Fraction(127, 5000)),
        name="inch",
        symbol="inch",
        aliases=("in",),
    )
)

rpm = mech.define_unit(
    name="revolutions_per_minute",
    symbol="rpm",
    expr=turn / minute,
    aliases=("rev_per_min",),
)

lbf = mech.define_unit(
    name="pound_force",
    symbol="lbf",
    expr=Quantity(Fraction("0.45359237") * Fraction("9.80665"), N),
)

psi = mech.define_unit(
    name="pound_per_square_inch",
    symbol="psi",
    expr=lbf / (inch**2),
)

ksi = mech.define_unit(
    name="kilopound_per_square_inch",
    symbol="ksi",
    expr=1000 * psi,
)

from unitflow.core.display import default_resolver
default_resolver.register_derived(rpm)
default_resolver.register_derived(lbf)
default_resolver.register_derived(psi)
default_resolver.register_derived(ksi)
