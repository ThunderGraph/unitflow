# Unitflow Brainstorm

## Status

This document is exploratory.
It captures the problem framing, product philosophy, and early design space.

When this document conflicts with later design docs, the later docs should win.

Current precedence:

1. `docs/architecture-decisions.md`
2. `docs/backend-methodology.md`
3. `docs/api-sketch.md`
4. `docs/brainstorm.md`

## Context

`unitflow` is being created to support `ThunderGraph-Model`.

ThunderGraph is intended to be an AI-powered MBSE environment built around a custom Python DSL rather than traditional SysML-style dead model notation.
The goal is to create executable system models with elegant attributes, constraints, inference, and links to simulation tools, metamodels, and digital twin workflows.

In that ecosystem, `unitflow` is not just a convenience library for unit conversion.
It is part of the semantic computation layer of the modeling system.

## Why This Exists

The immediate motivation is not "Python needs another units package."

The immediate motivation is:

- executable engineering models
- elegant attribute expressions
- unit-safe constraint expressions
- symbolic and dimensional reasoning across a system model
- solver-friendly representations of engineering relationships
- simulation and metamodel interoperability
- distributed compute support for digital twin workflows

That context should shape every major design choice.

## Primary Use Cases

The most important use cases are not generic quantity manipulation.
They are model-centric.

### 1. Executable Model Attributes

Engineers should be able to write clean, direct model expressions such as:

```python
shaft.speed = 3000 * rpm
motor.torque = 12 * N * m
power = motor.torque * shaft.angular_velocity
```

The code should read naturally inside a modeling DSL and should not feel like a wrapped utility API.

### 2. Constraint Expressions Across A System Model

System models should be able to express relationships such as:

```python
power == voltage * current
stress == force / area
flow_rate == velocity * area
```

These expressions should be validatable, composable, and suitable for later solving or execution.

### 3. Solvable Engineering Relationships

Expressions should support more than evaluation.
They should support reasoning.

That includes:

- dimensional validation
- symbolic representation
- partial evaluation
- solving for unknowns
- inference of required dimensions or units

### 4. Multi-Domain System Modeling

The library needs to support models spanning:

- mechanics
- electrical systems
- thermal systems
- fluids
- controls
- materials
- other engineering domains over time

This is a strong reason to separate a clean algebra core from extensible domain vocabularies.

### 5. Simulation And Metamodel Interoperability

Values and expressions should be able to cross tool boundaries cleanly.

That implies:

- explicit units and dimensions
- trustworthy conversions
- metadata that survives handoff
- adapters to simulation and modeling tools

### 6. Digital Twin And Distributed Compute Workflows

The target environment includes dynamic models, simulation coupling, and distributed execution.

That means quantities may be:

- scalar
- symbolic
- array-valued
- lazy
- streamed
- distributed

This makes array and distributed-compute compatibility a core requirement, not a bonus feature.

## Design Implications

If the primary use cases above are real, then several design implications follow.

- `unitflow` must be expression-friendly, not just value-friendly
- dimensions are part of model semantics, not just conversion bookkeeping
- symbolic and dimensional reasoning are important to the product direction
- extensibility is mandatory because model domains and vocabularies will grow
- array and distributed workflows are part of the target operating environment
- the library must preserve semantics across system, solver, and simulation boundaries

## Goal

Build a Python library for mathematical and engineering computation with units.

The library should:

- support executable engineering models and constraints
- feel elegant in real Python code
- support unit algebra without ceremony
- compose naturally into larger computation graphs
- serve as a substrate for broader engineering math
- grow into a broad catalog of practical engineering units
- leave room for symbolic and dimensional reasoning
- work well with NumPy and array-oriented workflows

## Product Philosophy

This should not aim to be "Pint, but cleaner."

It should aim to be a beautiful engineering math substrate.

That means:

- expressions should read like the math engineers want to write
- the core should disappear into the background once imported
- composition should feel obvious, not framework-driven
- the library should reward correct reasoning instead of tolerating ambiguity
- the design should stay minimal at the center and expansive at the edges

The bar is not just correctness.
The bar is correctness with taste.

If users are doing mechanics, controls, circuits, fluids, optimization, simulation, or symbolic derivation, the library should feel like a natural mathematical layer rather than a utility wrapper around numbers.

## Design Values

Four words should anchor the project:

- elegant
- composable
- sexy in code
- foundational

More concretely:

- `elegant` means small mental models, consistent behavior, and little boilerplate
- `composable` means every object should participate naturally in larger expressions, functions, arrays, and domain libraries
- `sexy in code` means expressions should be pleasant to write and pleasant to read
- `foundational` means the core abstractions should support future engineering and scientific capabilities without needing to be replaced

## Non-Goal

The goal is not to ship the biggest possible pile of units.

The goal is to build a coherent algebraic foundation that happens to support a large and extensible unit ecosystem.

## Desired API Feel

The API should feel mathematical and lightweight.

Examples:

```python
from unitflow.si import N, Hz, m, s, kg

assert 6 * N * 8 * Hz == 48 * N * Hz
assert 10 * m / s == 36 * (m / s)  # illustrative only

force = 2 * kg * (9.81 * m / s**2)
```

Important constraint: Python still requires explicit `*`, `/`, and `==`.
So the goal is "math-like Python", not a custom DSL.

The guiding test for the API is:

- does it read cleanly in notebooks, scripts, and libraries?
- does it encourage good algebraic habits?
- does it remain readable when expressions get longer?

If an API choice is powerful but ugly, it is probably wrong for the center of the library.

## Core Model

Keep the core small and clean.

Primary concepts:

- `Dimension`: physical dimension algebra
- `Unit`: scale + dimension + metadata such as name and symbol
- `Quantity`: magnitude + unit

Recommended design principles:

- immutable core objects
- explicit conversion
- strong dimensional correctness
- clean operator overloading
- minimal hidden global state
- simple enough to be trusted when embedded into larger systems

The core should be small enough that users can understand it quickly and stable enough that other libraries can safely build on top of it.

## Dimensional Representation

Represent dimensions as fixed exponent vectors over base dimensions.

Example SI basis:

- length
- mass
- time
- current
- temperature
- amount
- luminous intensity

This keeps equality, hashing, multiplication, division, and powers simple and fast.

## Unit Algebra

The unit system should support:

- unit multiplication
- unit division
- unit powers
- quantity arithmetic
- compatibility checks
- conversion between equivalent units

Examples:

```python
speed = 10 * m / s
accel = 9.81 * m / s**2
force = 2 * kg * accel
```

Publicly, users should mostly reason in terms of:

- units
- quantities

Composite units should "just work" without exposing too many internal implementation types.

The best API outcome is that users think in algebra, not in framework objects.

## Catalog Strategy

Separate the algebra engine from the unit catalogs.

Recommended split:

- `unitflow.core`
- `unitflow.si`
- `unitflow.domains.<domain>`

Likely domain packs:

- mechanical
- electrical
- thermo
- fluids
- materials
- controls
- rf

This keeps the engine small while allowing a broad unit library.

It also reinforces an important product boundary:

- the core is the substrate
- the catalogs are vocabulary packs built on top of the substrate

That distinction is what makes the project extensible instead of monolithic.

## Canonical Units And Aliases

Each unit should have a canonical identity plus aliases.

Example:

- canonical name: `meter`
- symbol: `m`
- alias: `metre`

This will help with:

- lookup
- parsing
- documentation
- serialization
- avoiding duplicate definitions

## Import Ergonomics

Two import styles seem useful.

Convenience:

```python
from unitflow.si import N, Hz, m, s

x = 6 * N * 8 * Hz
```

Scalable:

```python
from unitflow import si, mech

x = 6 * si.N * 8 * si.Hz
y = 3000 * mech.rpm
```

Namespace-based access will likely age better once the catalog becomes large.

This also helps preserve elegance as the ecosystem grows.
The main API should stay clean even if the library eventually ships hundreds or thousands of unit definitions.

## Unit Definition Style

Use declarative unit definitions instead of hand-writing behavior for every unit.

Example:

```python
newton = define_unit(
    name="newton",
    symbol="N",
    expr=kg * m / s**2,
    domain="si",
)
```

And:

```python
rpm = define_unit(
    name="revolution_per_minute",
    symbol="rpm",
    expr=cycle / minute,
    domain="mechanical",
)
```

The catalog should be mostly data, not bespoke logic.

This matters for extensibility as much as maintainability.
If unit definition is declarative and uniform, both library authors and end users can extend the system without needing to understand internals deeply.

## Extensibility

Extensibility should be a first-class design requirement, not an afterthought.

Users should be able to:

- define their own units
- define aliases and preferred symbols
- publish domain-specific packs on top of the core
- add custom registries or namespaces without forking the library
- attach metadata needed by downstream engineering software

The library itself should be able to:

- ship new domain packs without changing core semantics
- evolve formatting and parsing independently from algebra
- support optional symbolic and NumPy integrations as layers

### Desired Extension Experience

Defining a new unit should feel lightweight and obvious.

Example:

```python
from unitflow import define_unit
from unitflow import si

ksi = define_unit(
    name="kilopound_per_square_inch",
    symbol="ksi",
    expr=1000 * si.lbf / si.inch**2,
    aliases=("kip_per_square_inch",),
    domain="materials",
)
```

Creating a custom pack should also be straightforward.

Example direction:

```python
from unitflow import UnitNamespace, define_unit
from unitflow import si

aero = UnitNamespace("aero")
aero.knot = define_unit(name="knot", symbol="kn", expr=1852 * si.m / si.hour)
aero.ft = define_unit(name="foot", symbol="ft", expr=0.3048 * si.m)
```

This does not require a fork, special plugin framework, or core modification.

### Extension Model

The extension model should likely support:

- local ad hoc definitions inside user code
- reusable internal company libraries
- first-party domain packs shipped by `unitflow`
- third-party packages that register units or namespaces

That suggests the core should expose stable primitives for:

- defining units
- defining aliases
- grouping units into namespaces or registries
- exporting/importing catalog definitions
- validating collisions and compatibility

### Registry Philosophy

Avoid forcing everything through one magical global registry.

A better model is:

- a small default convenience namespace for common usage
- explicit namespaces or registries for serious applications
- clear composition rules when multiple packs are loaded

This keeps the library ergonomic for simple use and predictable for larger engineering systems.

## NumPy Direction

NumPy support makes sense, but it should be phased.

Recommended order:

1. allow NumPy arrays as quantity magnitudes
2. support a selective set of ufunc behaviors
3. add broader interoperability only when needed

Early rules should include:

- `add` and `subtract` require compatible units
- `multiply` and `divide` combine units
- `exp`, `log`, and trig functions should require dimensionless inputs
- reductions like `sum` and `mean` should preserve units where appropriate

## Array And Distributed Workflow Philosophy

Real engineering computation does not stop at scalar arithmetic.

If `unitflow` is going to matter in production engineering and scientific workflows, it must compose with:

- arrays
- lazy arrays
- labeled arrays
- distributed execution
- plotting and reporting boundaries

This should be treated as a foundational design requirement, not a later integration task.

### Core Requirement

`Quantity` should be designed around a generic magnitude.

That magnitude may be:

- a Python scalar
- a `numpy.ndarray`
- a `dask.array.Array`
- eventually other duck-array or symbolic types

This is one of the most important design choices in the whole library.
It ensures the algebra is not scalar-only and keeps the core suitable for serious computation.

### Design Rule

The same algebra should work across:

- scalar quantities
- array quantities
- lazy quantities
- labeled quantities

The library should not have one pleasant scalar API and a separate awkward "array mode."
There should be one model with different magnitude backends.

### NumPy Is The First Real Integration

NumPy is not just another optional ecosystem target.
It is the base layer for most of the scientific Python stack.

Strong NumPy support likely requires:

- `__array_ufunc__`
- `__array_function__`
- correct broadcasting behavior
- correct reduction behavior
- dimension checks for transcendental functions
- unit propagation for multiplicative operations

If this layer is designed well, much of the rest of the ecosystem becomes easier.

### Dask Requires Laziness Discipline

Dask support is less about special Dask features and more about not violating lazy execution.

That means the library should avoid:

- eager coercion to NumPy arrays
- hidden materialization of magnitudes
- conversions that require loading full data
- formatting or inspection paths that accidentally force computation

Operations on Dask-backed quantities should preserve laziness whenever possible.

### Xarray Should Be A First-Class Integration Target

For real engineering and scientific workflows, `xarray` may matter more than `pandas`.

Why:

- labeled dimensions
- coordinates
- datasets
- compatibility with Dask-backed computation
- common use in simulation, sensing, gridded data, and scientific pipelines

This suggests `unitflow` should eventually provide a deliberate `xarray` integration layer rather than treating xarray support as incidental.

### Plotting Is A Boundary Concern

Libraries like `matplotlib` matter, but they should mostly shape adapter design rather than core algebra design.

Useful plotting support likely means:

- converting values to display units at the boundary
- producing correct unit labels
- making common plotting workflows straightforward

The core should remain algebraic and clean rather than being distorted by plotting-specific behavior.

### Pandas Is Useful But Not The Center

Pandas support is valuable, but it should not drive the core model.

Tabular workflows are important, yet the strongest long-term computational path is likely:

- NumPy
- Dask
- xarray

Pandas can be supported well after the array and labeled-array story is solid.

### Performance And Purity

To support serious workflows, unit operations should be:

- pure
- predictable
- cheap in metadata handling
- careful about unnecessary conversions

The library should avoid turning unit correctness into a performance tax that makes large-scale workflows impractical.

### Architectural Implication

This points toward a clear layering strategy:

1. generic magnitude-aware core algebra
2. strong NumPy protocol support
3. lazy-safe behavior for Dask-backed magnitudes
4. dedicated xarray integration layer
5. plotting adapters
6. pandas support where useful

This order is important because the later integrations depend heavily on the earlier design being correct.

## Symbolic Reasoning

Symbolic support does make sense, but only in a focused way.

The library should probably own:

- unit algebra
- dimensional analysis
- compatibility checking
- native expression trees for engineering relationships
- dimensional inference

The library should probably not own:

- general symbolic simplification
- equation solving
- calculus
- a full CAS

For now, the design direction is to build a small native symbolic model first rather than designing around an external symbolic package.

This keeps the library aligned with its real role:

- own units
- own dimensions
- own dimensional reasoning

Not:

- become a full symbolic math platform itself

## Promising Symbolic Features

Most valuable symbolic features discussed so far:

- native `Symbol`, `Expr`, and constraint objects
- dimension-aware symbols
- dimensional validation of expressions
- dimensional inference for unknowns

Example direction:

```python
x = symbol("x", unit=m)
t = symbol("t", unit=s)
v = x / t
```

This supports "dimensional reasoning" without turning the project into a full symbolic math engine.

That is likely the right long-term posture for the project.
The symbolic layer should make the substrate more powerful, not make the core conceptually heavy.

## Strong Recommendation For Scope

Build in layers:

1. solid dimension algebra
2. clean quantity arithmetic and conversion
3. curated SI and domain unit catalogs
4. NumPy array magnitudes and selective interoperability
5. symbolic and dimensional reasoning as an optional layer

## Explicit Deferrals

Avoid forcing these into the earliest versions:

- full symbolic engine
- logarithmic units such as `dB` or `dBm`
- affine units such as `degC` or `degF`
- huge flat imports of every known unit
- broad support for every NumPy function from day one

These are important, but they complicate the core quickly.

Another explicit deferral:

- building a grand plugin architecture before the primitive extension story is proven

The first version should make extension possible through good primitives, not through a giant framework.

## Current Design Direction

The current preferred direction is:

- small immutable algebra core
- unit and quantity overloading for a math-like Python API
- large unit catalog built as separate declarative definitions
- domain-specific unit packs
- first-class extensibility for user-defined units and third-party packs
- symbolic and dimensional reasoning through a dedicated layer
- a small native expression/constraint model before any external symbolic interop

In other words:

- build a beautiful center
- build clean extension seams
- let the ecosystem grow around that center

## Open Questions

- What should the public `is_close(...)` API look like for scalars, arrays, and symbolic-adjacent workflows?
- What should the initial error hierarchy and serialization story look like for quantities, expressions, and constraints?
- Should `quantity_kind` stay a lightweight string in v1, or start as a typed namespace from the beginning?
- How much unit-family metadata around pseudo-dimensionless units should be exposed publicly versus kept as an internal backend concern?
