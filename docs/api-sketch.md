# Unitflow API Sketch

## Purpose

This document sketches a plausible public API for `unitflow` based on current architecture decisions.

It is not a final specification.
It is a pressure test for the syntax, object boundaries, and modeling ergonomics.

The goal is to answer:

- does the API feel elegant?
- does it support ThunderGraph-style executable modeling?
- does it preserve a clean separation between concrete values and symbolic expressions?
- does the constraint syntax feel natural enough to justify the operator overloading?

## Design Assumptions

This sketch assumes the following decisions:

- `Quantity` and `Expr` are separate concepts
- symbols may carry a `unit`, a `dimension`, or both
- optional `quantity_kind` metadata is separate from `dimension`
- symbolic comparisons build constraints
- constraint composition uses `&` and `|`
- namespaces are the default architectural style
- SymPy is out of scope for now

## Public Concepts

The first public surface should stay small.

Likely concepts:

- `Quantity`
- `Unit`
- `Dimension`
- `Symbol`
- `Expr`
- `Equation`
- `StrictInequality`
- `NonStrictInequality`
- `Constraint`
- `ConstraintSet` or `LogicalConstraint`
- unit namespaces such as `si`, `mech`, and `elec`

## Core Construction API

### Units And Quantities

Concrete quantities should feel direct and unsurprising.

```python
from unitflow import si, mech

length = 3 * si.m
speed = 10 * si.m / si.s
stress = 35 * mech.psi
```

Composite units should remain natural:

```python
force = 12 * si.N
frequency = 8 * si.Hz
result = 6 * si.N * 8 * si.Hz
assert result == 48 * si.N * si.Hz
```

### Symbols

Symbols represent model-bound or unknown values.

Unit-first:

```python
speed = symbol("speed", unit=si.m / si.s)
```

Dimension-first:

```python
drag_coeff = symbol("drag_coeff", dimension=dimensionless)
```

Both:

```python
torque = symbol("torque", unit=si.N * si.m, quantity_kind="torque")
```

### Expressions

Expressions should arise naturally from operations on symbols, quantities, or both.

```python
distance = speed * time
power = torque * omega
stress = force / area
```

These should evaluate to `Expr` when any participating operand is symbolic.

Type promotion rule:

- `Quantity op Quantity -> Quantity`
- anything symbolic in the operation promotes the result to `Expr`

## Constraint API

### Equations

Symbolic equality should produce an equation object.

```python
power = symbol("power", unit=si.W)
voltage = symbol("voltage", unit=si.V)
current = symbol("current", unit=si.A)

eq = power == voltage * current
```

Possible mental model:

- `power` is a `Symbol`
- `voltage * current` is an `Expr`
- `eq` is an `Equation`

### Inequalities

Relational operators should build inequality constraints.

```python
stress = symbol("stress", unit=si.Pa)
allowable = symbol("allowable", unit=si.Pa)

limit = stress <= allowable
```

Strict form:

```python
margin = stress < allowable
```

Negation should use `~`:

```python
safe_region = ~((stress > allowable) | (temperature > limit_temperature))
```

### Constraint Composition

Conjunction should use `&`:

```python
bounds = (0 * si.m <= x) & (x <= 10 * si.m)
```

Disjunction should use `|`:

```python
mode_rule = (mode_a_force == force) | (mode_b_force == force)
```

Larger sets should remain readable:

```python
constraints = (
    (0 * si.Pa <= pressure)
    & (pressure <= vessel.max_pressure)
    & (temperature <= vessel.max_temperature)
)
```

### Unsupported Boolean Coercion

This should be invalid:

```python
if pressure <= vessel.max_pressure:
    ...
```

This should also be invalid:

```python
(0 <= x) and (x <= 10)
```

The library should raise with a helpful error that points users to `&` and `|`.

### Conversion Naming

The API should use `.to(...)` consistently across concrete and symbolic objects.

Working direction:

- `Quantity.to(unit) -> Quantity`
- `Symbol.to(unit) -> Expr`
- `Expr.to(unit) -> Expr`

This is cleaner than splitting the concept across names like `.to(...)` and `.in_unit(...)`.

## Concrete vs Symbolic Behavior

One of the most important semantics in the API:

- pure concrete comparison returns `bool`
- if either operand is symbolic, comparison returns a constraint object

Examples:

```python
assert 3 * si.m == 300 * si.cm
```

```python
(3 * si.m) == (4 * si.m)   # bool
```

```python
power == voltage * current  # Equation
```

This split is deliberate.
It keeps ordinary calculations intuitive while preserving DSL sugar for modeling.

### Exact vs Inexact Numeric Comparison

Concrete `==` should not quietly become a tolerance-based engineering guess.

Working direction:

- exact-capable numeric types compare exactly after unit conversion
- inexact numeric types should use an explicit closeness API when tolerance matters

Example direction:

```python
force.is_close(19.62 * si.N)
```

This is safer than hiding tolerance policy inside `==`.

## Example Flows

## 1. Simple Numeric Engineering Calculation

```python
from unitflow import si

mass = 2 * si.kg
accel = 9.81 * si.m / si.s**2
force = mass * accel

force_in_newtons = force.to(si.N)
```

This is the minimum bar for basic usability.

## 2. Symbolic Constraint Authoring

```python
from unitflow import si, symbol

force = symbol("force", unit=si.N)
mass = symbol("mass", unit=si.kg)
accel = symbol("accel", unit=si.m / si.s**2)

constraint = force == mass * accel
```

This is the basic MBSE-friendly equation authoring form.

## 3. Bounded Variable

```python
from unitflow import si, symbol

x = symbol("x", unit=si.m)
bounds = (0 * si.m <= x) & (x <= 10 * si.m)
```

This is the canonical bounded form.
It intentionally replaces Python chained comparison syntax.

## 4. Alternative Constraints

```python
from unitflow import si, symbol

force = symbol("force", unit=si.N)
spring_force = symbol("spring_force", unit=si.N)
damper_force = symbol("damper_force", unit=si.N)

alternatives = (force == spring_force) | (force == damper_force)
```

This is useful for mode-dependent or architecture-dependent rules.

## 5. Mixed Concrete And Symbolic Expression

```python
from unitflow import si, symbol

area = 2 * si.m**2
pressure = symbol("pressure", unit=si.Pa)
force = pressure * area
```

This should produce an `Expr`, not a `Quantity`, because the result still depends on a symbol.

## 6. Domain Namespace Usage

```python
from unitflow import si, mech

shaft_speed = 3000 * mech.rpm
torque = 12 * si.N * si.m
omega = shaft_speed.to(si.rad / si.s)
power = torque * omega
```

This shows why namespace-first architecture scales better than a giant flat import surface.

This example also exposes a real backend requirement:

- `mech.rpm` must carry enough semantics to convert cleanly into angular-speed form
- the backend cannot treat all dimensionless-looking units as interchangeable noise

## 7. Semantic Display Ambiguity

Some dimensions admit multiple valid engineering displays.

Example:

```python
torque = symbol("torque", unit=si.N * si.m, quantity_kind="torque")
energy = symbol("energy", unit=si.J, quantity_kind="energy")
```

These may share the same physical dimension while still carrying different engineering meaning.

That implies the backend needs optional semantic metadata such as `quantity_kind`, especially for formatting and reporting.

## 8. Model-Oriented Example

This is the kind of shape the API should fit inside ThunderGraph:

```python
from unitflow import si, mech, symbol

shaft_speed = symbol("shaft_speed", unit=mech.rpm)
shaft_torque = symbol("shaft_torque", unit=si.N * si.m, quantity_kind="torque")
shaft_power = symbol("shaft_power", unit=si.W)

shaft_omega = shaft_speed.to(si.rad / si.s)
power_balance = shaft_power == shaft_torque * shaft_omega
speed_bounds = (0 * mech.rpm <= shaft_speed) & (shaft_speed <= 6000 * mech.rpm)
```

This reads much closer to executable engineering semantics than to a general-purpose units helper library.

It also makes the conversion step explicit instead of pretending `rpm` and `rad/s` are interchangeable without a defined rule.

## Suggested Minimal API Surface

If the first version is kept intentionally small, a very plausible public API could be:

```python
from unitflow import (
    si,
    mech,
    symbol,
    define_unit,
)
```

And the main user-facing behaviors would be:

- `number * unit -> Quantity`
- `unit * unit -> composite Unit`
- `symbol(...) -> Symbol`
- symbolic arithmetic -> `Expr`
- symbolic comparison -> `Constraint`
- constraint composition with `&`, `|`, and `~`

This is a strong minimal center.

## Open API Questions

The major questions that still need pressure testing are:

- Should the function be named `symbol(...)`, `var(...)`, or something more modeling-specific?
- Should `dimensionless` be a singleton or a helper from a `dimensions` namespace?
- Should `ConstraintSet` be a concrete public type, or should users mostly treat composed constraints opaquely?
- Should there be convenience helpers like `all_of(...)`, `any_of(...)`, and `between(...)`, even if `&` and `|` are the preferred syntax?
- Should symbols carry optional metadata such as descriptions, source model path, or solver hints from the beginning?
- Should `quantity_kind` use simple strings first, or a typed namespace such as `quantity_kinds.torque`?
- How much of the semantic metadata model should be exposed directly on quantities versus inferred from model context?

## Current Read On The API

The current syntax looks promising because it is:

- concise
- algebraic
- expressive enough for MBSE constraints
- readable in plain Python
- friendly to AI-generated code

If this direction holds up under more examples, it is likely a strong fit for the project.
