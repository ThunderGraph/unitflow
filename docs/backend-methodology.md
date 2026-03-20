# Unitflow Backend Methodology

## Purpose

This document captures the current backend methodology for how `unitflow` should process units, conversions, normalization, and result presentation.

The goal is not just mathematical correctness.
The goal is mathematical correctness that produces intuitive engineering results.

This matters because `unitflow` is intended to support:

- executable engineering models
- symbolic and dimensional reasoning
- engineering-facing calculation workflows
- downstream handoff to simulation tools, reports, and practitioners who require specific units

## Core Principle

Separate:

- semantic unit meaning
- default display form
- required output unit

These are related, but they are not the same thing.

If the backend collapses them into one concept, mixed-unit processing will become confusing and hard to control.

## Three Views Of A Quantity

Every quantity should be understood through three complementary views.

### 1. Semantic Form

This is the form the engine uses for correctness.

It should capture:

- dimension
- scale relative to a canonical basis
- later, unit kind if affine or logarithmic units are introduced

This form is used for:

- compatibility checks
- conversion
- equality
- symbolic normalization
- solver preparation

### 2. Default Display Form

This is the form shown to users when no explicit target unit has been requested.

The default display form should be:

- clean
- intuitive to engineers
- stable enough to be predictable
- free from ugly mixed authored compounds where possible

Example:

```python
3 * si.m * 33 * si.cm
```

should default to a clean area result such as:

```python
0.99 * si.m**2
```

not:

```python
99 * si.m * si.cm
```

### 3. Required Output Form

This is the form required by a consumer, contract, or workflow.

Examples:

- a machinist requires `mm`
- a stress report must be in `ksi`
- an interface contract requires `rpm`
- a downstream simulation adapter expects a specific unit system

This form must be explicitly requestable and must override the default display preference.

## Design Consequence

The backend should preserve semantic truth first, produce clean engineering defaults second, and support explicit delivery units whenever needed.

## Core Semantic Representation

The backend should treat units as immutable semantic objects.

Conceptually, a unit should carry:

- dimension
- scale
- canonical name
- symbol
- aliases
- optional formatting or display metadata

This does not require every unit to be reduced to a base-unit string at all times.
It does require every unit to have a reliable canonical semantic interpretation.

## Dimensions

Dimensions should be represented in a form that is:

- immutable
- hashable
- cheap to compare
- easy to combine under multiplication, division, and powers

The leading candidate remains a fixed exponent vector over base dimensions.

This enables:

- fast compatibility checks
- deterministic equality
- simple normalization logic

## Unit Conversion Methodology

For multiplicative units, conversion should follow a simple policy:

1. confirm the source and target units have the same semantic dimension
2. compute the scale ratio between them
3. apply that ratio to the magnitude
4. return a new quantity in the requested unit

Example:

```python
(3 * si.m).to(si.cm) == 300 * si.cm
```

This should be straightforward and deterministic.

## Exactness Of Definitions

Where practical, unit definitions should use exact ratios rather than floating approximations.

Examples:

- `cm = 1/100 m`
- `minute = 60 s`
- `inch = 0.0254 m`

This reduces accumulated conversion noise and improves trust in engineering calculations.

Magnitudes may still be floats, arrays, or other numeric types.
The point is that unit definitions themselves should be as exact as practical.

### Working Representation For Scale Factors

This needs to be more concrete than "use exactness where practical."

The backend should not store definition scales as plain floats.

Chosen direction for v1:

- a scale factor is represented as an exact rational coefficient multiplied by integer powers of a small set of named exact constants
- the only named exact constant that v1 needs to support is `pi`

That means units such as:

- `cm = 1/100 m`
- `minute = 60 s`
- `turn = 2*pi*rad`

can be represented without immediate precision loss.

Conceptually:

- `cm` uses rational scale only
- `minute` uses rational scale only
- `turn` uses rational scale multiplied by `pi`

This is intentionally narrower than a general symbolic algebra system.
The point is to support exact engineering unit definitions, not to build a broad symbolic simplifier for scale factors.

## Arithmetic Methodology

The backend needs different policies for different classes of operations.

## Addition And Subtraction

Addition and subtraction require compatible dimensions.

Examples:

```python
3 * si.m + 33 * si.cm
```

is valid because both terms are lengths.

```python
3 * si.m + 2 * si.s
```

is invalid because the dimensions differ.

### Default Result Policy For Add/Sub

The default result should preserve a clean compatible unit.

A reasonable first policy is:

- convert the right operand into the left operand's unit
- perform the operation
- return the result in the left operand's unit

Example:

```python
3 * si.m + 33 * si.cm -> 3.33 * si.m
```

This is not globally optimal for every display case, but it is deterministic and easy to reason about.

Display contexts or explicit target units may override this later, but raw arithmetic should remain predictable.

## Multiplication And Division

Multiplication and division do not require compatible dimensions.

They should:

- combine dimensions algebraically
- combine scales algebraically
- compute a semantically correct result
- choose a clean default display form

Example:

```python
3 * si.m * 33 * si.cm
```

should produce a semantically correct area and default to a clean result such as:

```python
0.99 * si.m**2
```

not:

```python
99 * si.m * si.cm
```

The same principle applies more broadly:

- `12 * si.N * 2 * si.m` should prefer `24 * si.J`
- `1 * si.kg * si.m / si.s**2` should be semantically equivalent to `1 * si.N`

### When Semantic Normalization Happens

This needs to be explicit.

Semantic normalization should happen eagerly on every arithmetic operation.

That means each operation should immediately compute:

- the combined semantic dimension
- the combined exact scale signature
- any direct cancellation implied by multiplication, division, or powers

Examples:

- `(3 * si.m / si.s) * (2 * si.s)` should semantically normalize to a length result during the operation, not only later during formatting
- `si.m * si.cm` should semantically normalize to an area signature immediately even if the chosen display unit is resolved afterward

### When Display Resolution Happens

Display resolution does not need to be the same thing as semantic normalization.

Working policy:

- semantic normalization happens eagerly
- default display resolution happens when a result quantity is materialized
- the resolved display choice may be cached
- explicit `.to(...)` or evaluation-time target units override the default display choice

This keeps the math deterministic while avoiding repeated display heuristics on every print.

## Powers

Raising a unit-bearing quantity to a power should:

- raise the magnitude to that power
- multiply the unit exponents accordingly
- update the semantic dimension accordingly

Examples:

```python
(3 * si.m)**2 -> 9 * si.m**2
```

```python
(9 * si.m**2)**0.5 -> 3 * si.m
```

Restrictions and edge-case policies can be tightened later, but the basic rule should stay simple.

Invalid cases should fail loudly rather than guess.

Examples:

- incompatible fractional powers on unsupported unit forms
- invalid attempts to take powers that the numeric backend cannot represent cleanly

## Equality Methodology

Equality should compare semantic equivalence, not raw stored representation.

Example:

```python
1 * si.N == 1 * si.kg * si.m / si.s**2
```

should evaluate as true for concrete quantities.

Similarly:

```python
3 * si.m * 33 * si.cm == 0.99 * si.m**2
```

should also evaluate as true.

This is one of the strongest reasons to keep semantic normalization distinct from display choice.

### Exact vs Inexact Equality

The operator `==` should not quietly smuggle in tolerance heuristics.

Working policy:

- exact-capable numeric types should compare exactly after unit conversion
- inexact numeric types should support an explicit closeness API

Concrete semantics for `==`:

- convert one operand into the other's unit using exact unit-scale semantics
- compare the resulting magnitudes with the backend numeric type's normal equality operator
- do not apply tolerance automatically

This means float-backed quantities may compare false even when they are engineering-close.
That is intentional.

Example direction:

```python
force.is_close(19.62 * si.N)
```

This is safer than making `==` mean approximate equality for floats and arrays.

## Default Display Selection

The default display layer should choose units that are understandable and not visually awkward.

### Initial Policy

A reasonable first-pass display policy is:

1. prefer a named derived unit when there is a clean known match and no semantic ambiguity
2. otherwise prefer a coherent normalized compound unit
3. avoid mixed authored compounds like `m * cm`
4. prefer powers over repeated factors
5. preserve sign and magnitude clearly without clever formatting tricks

Examples:

- `kg*m/s^2` may display as `N`
- `N/m^2` may display as `Pa`
- `m*cm` should display as `m^2`
- `m/s * s` should simplify toward `m`

The backend should support this without turning display selection into a magical or unpredictable system.

### Semantic Display Ambiguity

Dimensionally equivalent units are not always semantically interchangeable from an engineering-display perspective.

The classic example is:

- `N*m` for torque
- `J` for energy

These share the same physical dimension but are not the same engineering concept.

Working methodology:

- do not auto-prefer a named derived unit when the mapping is semantically ambiguous
- allow optional semantic hints such as `quantity_kind`, display family, or model-context hint
- when no reliable semantic hint exists, prefer the coherent compound unit over a potentially misleading named derived unit

This means:

- torque may continue to display as `N*m`
- energy may display as `J`

even though the semantic dimension system recognizes them as dimensionally equivalent

### Pseudo-Dimensionless Units

The backend must also deal with units that are dimensionless in base SI algebra but not semantically meaningless.

Important cases include:

- `rad`
- `sr`
- `cycle`
- `turn`

Chosen v1 methodology:

- treat these as truly dimensionless in the core dimension vector algebra
- preserve unit-family metadata such as `angle`, `solid_angle`, or `cycle_count`
- unit-family metadata does not affect base compatibility or conversion legality by itself
- support explicit exact definitions such as `turn = 2*pi*rad`

This is necessary so that:

- trigonometric functions can still enforce appropriate inputs
- angular velocity can be represented cleanly
- units such as `rpm` can convert correctly into `rad/s`

This is a deliberate trade-off.
The algebra stays simple, while semantic families carry the extra information needed for display and selected validation behavior.

## Explicit Output Unit Control

The backend must support explicit control over final units.

This is essential for engineering handoff workflows.

Examples:

```python
area = 3 * si.m * 33 * si.cm
area.to(si.mm**2)
```

and conceptually:

```python
result = evaluate(expr, target_unit=si.mm**2)
```

This is different from the default display system.
It is a hard requirement from a consuming context.

## Result Unit Policy

The result unit policy should therefore have two modes:

### 1. No Explicit Target Unit

When no explicit output unit is requested:

- compute semantically
- choose a clean default engineering display

### 2. Explicit Target Unit Requested

When an explicit output unit is requested:

- verify dimensional compatibility
- convert exactly into that requested unit
- return the result in that unit

This policy reflects real engineering workflows better than blindly preserving authored mixed-unit expressions.

## Expression-Level Conversion

Quantities need explicit conversion.
Expressions likely do as well.

That is especially important when authored units are convenient for users but solver or reporting semantics require a different unit form.

Example:

```python
shaft_omega = shaft_speed.to(si.rad / si.s)
```

The public API should use `.to(...)` consistently across quantities, symbols, and expressions.
The return type may differ by object category, but the verb should stay the same.

## Named Derived Units

Named derived units should not be special-case algebra objects.

They should be normal units whose semantic form matches a known composite basis.

Examples:

- `N`
- `Pa`
- `J`
- `W`
- `Hz`

This keeps the algebra engine uniform and lets the display layer prefer concise engineering notation when appropriate.

## Symbolic And Constraint Processing

The same semantic methodology should support the symbolic side of the system.

That means:

- expressions should normalize according to semantic dimensions and scales
- constraint validation should use semantic form
- solver preparation should work from normalized semantics
- user-facing output can still preserve preferred or required units

This is especially important for ThunderGraph, where expressions are not just evaluated but also reasoned about.

## Error Behavior

The backend should fail explicitly and consistently on invalid operations.

At a minimum, the design should plan for distinct error categories such as:

- incompatible dimensions for add/subtract
- incompatible target units for conversion
- invalid unit powers
- invalid boolean coercion of constraint objects
- unresolved or unsupported unit definitions

The exact class names can be decided later, but the methodology should assume a real error hierarchy rather than generic exceptions everywhere.

## Serialization Boundary

Because the target environment includes distributed execution and digital twin workflows, serialization cannot be an afterthought.

Working direction:

- quantities should serialize structurally rather than relying only on pickle
- expressions and constraints should serialize as typed trees
- serialization should preserve canonical unit identity and any explicit display-unit or semantic-kind hints

This does not require freezing a wire format yet, but it does mean the internal model should remain serializable by design.

## Array And Distributed Backends

This methodology is also intended to compose with array and distributed workflows.

Why it helps:

- semantic metadata is small and immutable
- conversion factors are local and deterministic
- units can remain decoupled from the storage backend of the magnitude
- explicit output-unit conversion can happen without changing the conceptual model

This supports future use with:

- NumPy
- Dask
- xarray
- simulation adapters

## Out Of Scope For Initial Backend Methodology

The initial methodology should focus on multiplicative units.

Explicitly deferred:

- affine units such as `degC` and `degF`
- logarithmic units such as `dB` and `dBm`
- context-dependent equivalencies
- aggressive display heuristics beyond obvious clean simplification

These cases matter, but they should not complicate the first clean semantic core.

## Summary

The backend methodology should follow these principles:

1. semantic correctness comes first
2. default display should be clean and engineering-friendly
3. explicit output units must be supported
4. additive and multiplicative operations need different result policies
5. equality should be semantic, not representation-based
6. named units are display conveniences over a uniform semantic engine
7. the backend should remain compatible with symbolic, array, and distributed workflows

This is the intended foundation for a unit system that is both elegant in code and useful in real engineering practice.
