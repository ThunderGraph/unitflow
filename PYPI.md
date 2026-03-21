# UnitFlow

**Elegant engineering math for Python.**

Unit algebra. Dimensional reasoning. Symbolic constraints. Array workflows.
Built for engineers who refuse to compromise on correctness or beauty.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/type--checked-mypy-blue.svg)](https://mypy-lang.org/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

## Installation

```bash
pip install unitflow
```

For NumPy support:

```bash
pip install unitflow[numpy]
```

The core library has **zero dependencies**. NumPy is optional.

## Quick Start

```python
from unitflow import m, cm, kg, s, N, kW, MW, rpm, rad, si

# Intuitive arithmetic
force = 2 * kg * 9.81 * (m / s**2)
print(force.to(N))              # 19.62 N

# Exact conversions across orders of magnitude
power = 5000 * si.W
print(power.to(kW))             # 5 kW
print(power.to(MW))             # 0.005 MW

# Angular speed with exact pi-bearing scale factors
angular = (3000 * rpm).to(rad / s)
print(angular)                  # 314.159... rad/s

# Semantic equality: same physics, same object
assert 1 * m == 100 * cm
assert hash(1 * m) == hash(100 * cm)
```

## Features

- **Clean Unit Algebra** -- Immutable, composable units with automatic dimension tracking.
- **Exact Scale Representation** -- Rational arithmetic with explicit pi support. No floating-point drift.
- **SI Prefix System** -- Every standard prefix from pico to tera, generated programmatically.
- **Torque vs Energy Disambiguation** -- Same dimension, different meaning. UnitFlow knows the difference.
- **Symbolic Constraints** -- Define equations and inequalities as first-class Python objects for MBSE.
- **NumPy Integration** -- Array-backed quantities via `__array_ufunc__` and `__array_function__`.
- **JSON-Safe Serialization** -- Quantities and constraint trees serialize to plain dicts.
- **Explicit Errors** -- Dimension mismatches and incompatible conversions fail loudly. No silent corruption.

## Symbolic Constraints

```python
from unitflow import symbol, N, kg, m, s, W, rpm, rad

F = symbol("F", unit=N)
mass = symbol("m", unit=kg)
a = symbol("a", unit=m / s**2)

newtons_law = F == mass * a          # Returns an Equation, not a bool

x = symbol("x", unit=m)
bounds = (0 * m <= x) & (x <= 10 * m)  # Conjunction of constraints
```

## User-Defined Units

```python
from unitflow import define_unit, UnitNamespace, Quantity, m, s, generate_prefixes
from fractions import Fraction

ft = define_unit(name="foot", symbol="ft", expr=Quantity(Fraction(3048, 10000), m))
print((6 * ft).to(m))  # 1.8288 m

aero = UnitNamespace("aero")
knot = aero.define_unit(name="knot", symbol="kn", expr=Quantity(Fraction(1852, 3600), m / s))
generate_prefixes(aero, knot, include={"milli", "kilo"})
```

## Part of ThunderGraph

UnitFlow is the foundational math layer for [ThunderGraph](https://www.thundergraph.ai/), an AI-powered model-based systems engineering platform.

## Links

- [GitHub Repository](https://github.com/ThunderGraph/unitflow)
- [Full Documentation & Examples](https://github.com/ThunderGraph/unitflow/blob/main/README.md)
- [Contributing Guide](https://github.com/ThunderGraph/unitflow/blob/main/CONTRIBUTING.md)

## License

Apache 2.0
