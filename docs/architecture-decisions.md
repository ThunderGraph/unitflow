# Unitflow Architecture Decisions

## Purpose

This document captures architecture decisions that are firm enough to guide early design and implementation.

These decisions are being made in the context of `ThunderGraph-Model`, where `unitflow` is intended to support:

- executable engineering models
- elegant model attribute expressions
- symbolic and dimensional reasoning
- constraint definition and solving
- future simulation and digital twin workflows

The goal is not to build a generic units utility with endless features.
The goal is to build a beautiful engineering computation substrate.

## Core Positioning

`unitflow` is not being designed to compete head-on with general-purpose units libraries.

It is being designed as:

- a unit and dimension system
- an expression substrate for engineering math
- a constraint-authoring layer
- a semantic foundation for executable MBSE

That product direction should win every architecture argument unless there is a compelling reason otherwise.

## Decision: Separate `Quantity` And `Expr`

Concrete values and symbolic/model expressions will be separate public concepts.

Planned shape:

- `Quantity`: concrete magnitude plus unit
- `Expr`: symbolic or model-bound expression

Why:

- concrete arithmetic should stay simple and predictable
- symbolic reasoning should not pollute every concrete value path
- model expressions need different behavior than plain numeric quantities
- the separation creates a clean solver boundary

Example:

```python
length = 3 * si.m          # Quantity
speed = symbol("speed", unit=si.m / si.s)
time = symbol("time", unit=si.s)

distance = speed * time    # Expr
```

This separation is intentional and desirable.

## Decision: Symbols May Carry A Unit, A Dimension, Or Both

Symbols should support any of the following:

- `unit`
- `dimension`
- both

Rules:

- at least one of `unit` or `dimension` is required
- if only `unit` is given, infer `dimension`
- if only `dimension` is given, the symbol has no preferred display unit
- if both are given, they must agree

Why:

- engineers often think in concrete units
- dimensional analysis is a first-class goal
- display preference and semantic dimensional identity are related but not identical

Examples:

```python
speed = symbol("speed", unit=si.m / si.s)
```

```python
drag_coeff = symbol("drag_coeff", dimension=dimensionless)
```

```python
torque = symbol("torque", unit=si.N * si.m, quantity_kind="torque")
```

This gives both ergonomic model authoring and strong dimensional semantics.

## Decision: Quantity Kind Is Separate From Dimension

Some engineering concepts share the same physical dimension but should not collapse to the same display or reporting meaning.

Examples:

- torque vs energy
- angle vs plain dimensionless ratios

Working direction:

- `dimension` participates in compatibility and conversion
- `quantity_kind` is optional semantic metadata
- `quantity_kind` does not change unit algebra
- `quantity_kind` may influence display, reporting, and domain-specific validation

This keeps the algebra clean while still acknowledging real engineering meaning.

## Decision: Overloaded Relational Operators Build Constraints

The symbolic API will support relational operator sugar.

Intended mapping:

- `a == b` -> `Equation`
- `a < b` -> `StrictInequality`
- `a <= b` -> `NonStrictInequality`
- `a > b` -> `StrictInequality`
- `a >= b` -> `NonStrictInequality`

Examples:

```python
eq = power == voltage * current
```

```python
limit = stress <= allowable_stress
```

```python
positive_mass = mass > 0 * si.kg
```

Why:

- it reads like engineering math
- it makes the DSL expressive
- it improves authoring ergonomics for both humans and AI systems generating code

This is a deliberate syntax choice, not an accident.

## Decision: Constraint Composition Uses `&` And `|`

Constraint composition should support:

```python
(0 <= x) & (x <= 10)
```

and:

```python
(a == b) | (c == d)
```

This is the preferred syntax for conjunction and disjunction of constraints.

Why:

- it is compact and readable
- it preserves the mathematical feel of the DSL
- it composes well in generated code
- it works well for AI-assisted authoring and "vibecoding" workflows

Likely interpretation:

- `&` creates a logical conjunction of constraints
- `|` creates a logical disjunction of constraints

Potential resulting types:

- `Constraint`
- `Equation`
- `StrictInequality`
- `NonStrictInequality`
- `ConstraintSet` or `LogicalConstraint`

The exact class hierarchy can remain flexible for now, but the operator semantics should not.

## Decision: Constraint Negation Uses `~`

Logical negation should use bitwise-not syntax on constraint objects.

Examples:

```python
~(x <= 10 * si.m)
```

```python
~((a == b) | (c == d))
```

Why:

- Python `not` cannot be overloaded cleanly for symbolic objects
- `~` fits naturally with the `&` and `|` composition model
- it gives the DSL a complete basic logical operator set

Implementation note:

- simple relational constraints may normalize directly, such as `~(x <= y) -> x > y`
- compound constraints may remain tree-structured and be normalized later

## Decision: Chained Comparisons Are Not A Supported Primary Pattern

This style is attractive:

```python
0 <= x <= 10
```

But Python chained comparisons depend on boolean coercion and do not compose cleanly with symbolic constraint objects.

So the supported form will be:

```python
(0 <= x) & (x <= 10)
```

This should be treated as the canonical idiom.

If helpful later, convenience helpers like `between(x, 0, 10)` may be added, but the operator-based form is already good enough.

## Decision: Concrete Equality Remains Boolean

Concrete quantity comparison should still behave normally.

Examples:

```python
assert 3 * si.m == 300 * si.cm
```

```python
(3 * si.m) == (4 * si.m)   # bool
```

By contrast, symbolic or expression-bearing comparisons should produce constraint objects.

Examples:

```python
power == voltage * current   # Equation
```

```python
pressure <= max_pressure     # NonStrictInequality
```

Behavioral rule:

- pure concrete comparisons return `bool`
- if either operand is symbolic or expression-bearing, the result is a constraint object

This keeps normal engineering calculations unsurprising while preserving the DSL.

This rule must be implemented symmetrically so that:

```python
force == 5 * si.N
```

and:

```python
5 * si.N == force
```

produce equivalent constraint objects rather than depending on operand order.

## Decision: Arithmetic Promotion Follows Symbolic Dominance

The type result of arithmetic should be explicit rather than implicit.

Working rule:

- `Quantity op Quantity -> Quantity`
- `Quantity op Symbol -> Expr`
- `Quantity op Expr -> Expr`
- `Symbol op Symbol -> Expr`
- `Symbol op Expr -> Expr`
- `Expr op Expr -> Expr`

This ensures symbolic participation dominates concrete participation without forcing concrete arithmetic through the symbolic layer unnecessarily.

## Decision: Constraint Objects Must Not Behave Like Booleans

Constraint objects should raise immediately if Python tries to coerce them to `bool`.

Why:

- it prevents subtle bugs
- it makes unsupported idioms fail loudly
- it guides users toward the intended composition syntax

Examples of invalid patterns:

```python
if power == voltage * current:
    ...
```

```python
(0 <= x) and (x <= 10)
```

Examples of intended patterns:

```python
constraint = power == voltage * current
```

```python
bounds = (0 <= x) & (x <= 10)
```

```python
alternatives = (a == b) | (c == d)
```

```python
negated = ~(x <= 10 * si.m)
```

The error message should clearly explain that constraints are not booleans and should suggest `&`, `|`, and `~` where relevant.

## Decision: Namespaces Are The Architectural Default

Unit access should support both:

Architectural default:

```python
from unitflow import si, mech

speed = 10 * si.m / si.s
stress = 35 * mech.psi
```

Convenience import style:

```python
from unitflow.si import m, s, N
```

Why:

- namespaces scale better as the unit catalog grows
- they reduce collisions
- they make domain packs more coherent
- direct imports still remain available for concise code

This means the design should optimize for explicit namespaces while still offering convenient local imports.

## Decision: `define_unit(...)` Uses A Keyword-First Stable Signature

Unit definition examples should stop drifting across documents.

Working direction:

- prefer a keyword-first public API for `define_unit(...)`
- keep the core fields explicit: `name=`, `symbol=`, `expr=`
- add optional fields such as `aliases=`, `domain=`, and semantic metadata explicitly by keyword

Example:

```python
define_unit(
    name="knot",
    symbol="kn",
    expr=1852 * si.m / si.hour,
    domain="aero",
)
```

Why:

- it is clearer in docs
- it is more stable as the signature evolves
- it is friendlier to AI-generated code than positional-argument guessing

## Decision: Ignore SymPy For Now

SymPy is intentionally out of scope for the current architecture decisions.

This is not a rejection of interoperability forever.
It is a sequencing decision.

Why:

- `unitflow` needs to define its own model of expressions and constraints first
- bringing in SymPy too early could distort the design
- the current priority is to understand the native MBSE-oriented semantics

For now, the target direction is a small native symbolic model with concepts such as:

- `Symbol`
- `Expr`
- `Equation`
- `StrictInequality`
- `NonStrictInequality`

No attempt should be made yet to design the system around external symbolic tooling.

## Decision: Native Expression Scope Stays Intentionally Small

Ignoring SymPy does not mean trying to build a full computer algebra system.

The native expression layer should stay deliberately narrow in early versions.

It should support:

- expression trees
- dimensional validation
- substitution
- traversal
- canonical structural equality
- solver-friendly normalization

It should explicitly avoid early ambition around:

- deep symbolic simplification
- algebraic factorization
- calculus
- broad symbolic rewrite systems

This is a containment decision.
The native AST exists to support executable MBSE semantics, not to become a general symbolic math platform.

## Decision: Constraint Trees Are First-Class

Composed constraints should remain tree-structured objects that can be inspected and walked later by validation, serialization, and solver layers.

Examples:

```python
(a == b) | ((c <= d) & ~(e < f))
```

The exact public class names can evolve, but the model should preserve logical structure rather than flattening everything into opaque strings or solver-specific blobs.

## DSL Ergonomics As A First-Class Requirement

Syntax sugar is not a cosmetic concern.
It is part of the product.

This matters because `unitflow` is intended to be:

- pleasant for engineers to author directly
- easy for AI systems to generate correctly
- readable when embedded into a larger Python MBSE DSL

The following are explicitly considered good target syntax:

```python
shaft.speed = 3000 * mech.rpm
power == torque * omega
(0 <= x) & (x <= 10)
(a == b) | (c == d)
```

The architecture should protect and preserve this quality.

## Near-Term Consequences

These decisions imply the library will likely need:

- a concrete algebra core for `Quantity`
- a symbolic expression tree for `Expr`
- relational constraint types
- logical composition of constraints
- clear separation between concrete evaluation and symbolic authoring
- unit namespaces and extensible domain catalogs

These decisions do not yet lock down:

- exact class hierarchy
- solver architecture
- serialization format
- simulation adapters
- distributed execution implementation details

Those can be decided later without undoing the choices above.
