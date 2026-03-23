# unitflow Expression Layer Gaps for tg-model Phase 3

## Purpose

This document summarizes the specific capabilities that `unitflow`'s expression layer currently lacks and that `tg-model` Phase 3 (Dependency Planning and Synchronous Execution) requires. It is written against the actual `unitflow` source code, not assumptions.

## Context

`tg-model` Phase 3 needs to:

- build a bipartite dependency graph from authored expressions
- evaluate directed expressions against a dictionary of realized values
- evaluate constraint predicates against realized values
- hand equation sets to a solver backend (SymPy / SciPy) as fast numeric residual functions
- do all of the above while preserving `unitflow` dimensional safety at the boundaries

## Current state of unitflow expression layer

Reading: `unitflow/expr/expressions.py`, `unitflow/expr/symbols.py`, `unitflow/expr/constraints.py`, `unitflow/serialization/expressions.py`.

### What already works well

- **AST construction.** `Expr` subclasses (`AddExpr`, `MulExpr`, `DivExpr`, `SubExpr`, `PowExpr`, `ConversionExpr`, `QuantityExpr`) form a clean, frozen, immutable tree.
- **Symbol definition.** `Symbol` carries name, dimension, optional unit, optional `quantity_kind`.
- **Equation / constraint capture.** `Expr.__eq__` returns `Equation(Constraint)`, not a boolean. `__lt__`, `__le__`, `__gt__`, `__ge__` return typed constraint nodes. `__bool__` on `Constraint` raises `BooleanCoercionError`.
- **Logical composition.** `Conjunction`, `Disjunction`, `Negation` compose constraints.
- **Dimension tracking.** Every AST node exposes `.dimension` computed from its children.
- **Structural comparison.** `.is_same()` exists for deep structural equality.
- **Serialization.** `serialize_expr`, `deserialize_expr`, `serialize_constraint`, `deserialize_constraint` round-trip the full AST to JSON-safe dicts.
- **Reverse operators.** `__radd__`, `__rmul__`, etc. handle `Quantity * Expr` promotion correctly.

### What is missing

The following three capabilities do not exist anywhere in the current codebase.

---

## Gap 1: Free symbol extraction

### What tg-model needs

To compile the dependency graph, `tg-model` must look at any `Expr` or `Constraint` and ask: *"Which `Symbol` objects appear in this tree?"*

Without this, `tg-model` cannot draw dependency edges from value nodes (parameters/attributes) to compute nodes (expressions/constraints/solve groups).

### What unitflow currently provides

Nothing. There is no `free_symbols` property or method on `Expr`, `Constraint`, or any subclass.

The `serialize_expr` function in `serialization/expressions.py` already walks the full AST recursively. A `free_symbols` implementation would follow the same recursive pattern but collect `Symbol` instances instead of building dicts.

### Recommended addition

Add a `free_symbols` property to `Expr` and `Constraint` base classes.

Behavior:

- `Symbol.free_symbols` returns `frozenset({self})`
- `QuantityExpr.free_symbols` returns `frozenset()`
- Binary nodes (`AddExpr`, `MulExpr`, etc.) return `self.left.free_symbols | self.right.free_symbols`
- `PowExpr.free_symbols` returns `self.base.free_symbols`
- `ConversionExpr.free_symbols` returns `self.expr.free_symbols`
- `Equation` / inequality `.free_symbols` returns `self.left.free_symbols | self.right.free_symbols`
- `Conjunction` / `Disjunction` `.free_symbols` returns `self.left.free_symbols | self.right.free_symbols`
- `Negation.free_symbols` returns `self.constraint.free_symbols`

Return type should be `frozenset[Symbol]` for immutability.

### Estimated scope

Small. One property per AST node class, following the same recursive pattern already used by `is_same()` and `serialize_expr()`.

---

## Gap 2: Context-based evaluation (substitute and compute)

### What tg-model needs

When the execution engine runs a directed compute node, it has a dictionary of realized values keyed by `Symbol`:

```python
context = {shaft_speed_sym: Quantity(3000, rpm), shaft_torque_sym: Quantity(50, N * m)}
result = expr.evaluate(context)  # -> Quantity
```

This must:

- recursively substitute `Symbol` nodes with their bound `Quantity` values
- perform the arithmetic using `Quantity` operations (preserving dimensional safety)
- return a concrete `Quantity` when all symbols are bound
- raise a clear error if any symbol is unbound

### What unitflow currently provides

Nothing. There is no `evaluate`, `subs`, `substitute`, or equivalent method on `Expr`.

`Quantity` already supports full arithmetic (`__add__`, `__mul__`, `__truediv__`, `__pow__`, `.to()`), so the evaluation logic would delegate to existing `Quantity` math once symbols are replaced.

### Recommended addition

Add an `evaluate(context: dict[Symbol, Quantity]) -> Quantity` method to the `Expr` base class with recursive dispatch:

- `Symbol.evaluate(ctx)` — look up `self` in `ctx`, raise if missing
- `QuantityExpr.evaluate(ctx)` — return `self.value`
- `AddExpr.evaluate(ctx)` — `self.left.evaluate(ctx) + self.right.evaluate(ctx)`
- `SubExpr.evaluate(ctx)` — `self.left.evaluate(ctx) - self.right.evaluate(ctx)`
- `MulExpr.evaluate(ctx)` — `self.left.evaluate(ctx) * self.right.evaluate(ctx)`
- `DivExpr.evaluate(ctx)` — `self.left.evaluate(ctx) / self.right.evaluate(ctx)`
- `PowExpr.evaluate(ctx)` — `self.base.evaluate(ctx) ** self.power`
- `ConversionExpr.evaluate(ctx)` — `self.expr.evaluate(ctx).to(self.target_unit)`

Add an `evaluate(context: dict[Symbol, Quantity]) -> bool` method to `Constraint` subclasses:

- `Equation.evaluate(ctx)` — `self.left.evaluate(ctx).is_close(self.right.evaluate(ctx))` or a residual-based check
- `StrictInequality.evaluate(ctx)` — compare magnitudes after unit normalization
- `NonStrictInequality.evaluate(ctx)` — same
- `Conjunction.evaluate(ctx)` — `self.left.evaluate(ctx) and self.right.evaluate(ctx)`
- `Disjunction.evaluate(ctx)` — `self.left.evaluate(ctx) or self.right.evaluate(ctx)`
- `Negation.evaluate(ctx)` — `not self.constraint.evaluate(ctx)`

### Estimated scope

Medium. The recursive dispatch is straightforward (mirrors `serialize_expr` pattern), but the constraint evaluation needs careful dimensional normalization and tolerance decisions.

---

## Gap 3: Numeric function compilation for solver backends

### What tg-model needs

When the execution engine runs a solve group, it hands equations to a solver backend (e.g. SciPy `root`). SciPy will call a residual function thousands of times per second. That function must operate on **bare floats**, not `unitflow` AST nodes or `Quantity` objects.

`tg-model` needs a way to compile a `unitflow` expression tree into a fast callable:

```python
# Before the solver loop (once)
residual_fn = expr.compile_numeric(
    symbols=[shaft_torque_sym, shaft_speed_sym],
    reference_units={shaft_torque_sym: N * m, shaft_speed_sym: rad / s},
)

# Inside the solver loop (thousands of times)
residual = residual_fn(50.0, 314.159)  # bare floats in, bare float out
```

This must:

- strip all unit overhead before the solver loop
- bake conversion factors into the compiled function where `ConversionExpr` or mismatched units appear
- return a plain `Callable[[float, ...], float]` that SciPy can call at full speed
- validate dimensional consistency once at compile time, not on every call

### What unitflow currently provides

Nothing. There is no compilation, code generation, or lambdify-style facility.

### Recommended addition

Add a `compile_numeric` function (module-level or method on `Expr`) that:

1. Takes an ordered list of symbols and a reference unit for each
2. Walks the AST once to build a Python function (or uses `eval` / closure construction)
3. Bakes `QuantityExpr` values into pre-converted float constants
4. Bakes `ConversionExpr` scale factors into pre-computed float multipliers
5. Returns a `Callable` that maps `(*float) -> float`

For constraints / equations, provide a residual compiler:

- `Equation` compiles to `lhs_fn(*args) - rhs_fn(*args)` (residual form)
- Inequalities compile to `lhs_fn(*args) - rhs_fn(*args)` with sign convention

### Estimated scope

Larger than Gaps 1 and 2. Requires careful handling of `ConversionExpr` scale factors and `QuantityExpr` constant folding. However, the AST is simple (no conditionals, no loops, no function calls beyond arithmetic), so the compilation is tractable.

### Performance note

If Python closure overhead is still too slow for very large solver problems, a future optimization path would be to emit a NumPy vectorized function or use `numba`. But for v0, a Python closure is sufficient.

---

## Summary

| Gap | Capability | Blocking for tg-model | Estimated scope |
|-----|-----------|----------------------|-----------------|
| 1 | `free_symbols` on `Expr` and `Constraint` | Phase 3 dependency graph compilation | Small |
| 2 | `evaluate(context)` on `Expr` and `Constraint` | Phase 3 directed evaluation and constraint checking | Medium |
| 3 | `compile_numeric(symbols, units)` on `Expr` / `Equation` | Phase 3 solve-group execution | Medium-Large |

All three gaps are blocking for `tg-model` Phase 3 and should be addressed in `unitflow` before or during early Phase 3 work.

## What does NOT need to change

- AST node structure — already clean and sufficient
- `Symbol` definition — already carries dimension, unit, and quantity_kind
- `Constraint` hierarchy — already correct
- Serialization — already works
- `Quantity` arithmetic — already unit-safe and exact
- `__eq__` returning `Equation` — already correct

The expression layer's **design** is solid. It just needs the three operational capabilities above to become a usable execution substrate for `tg-model`.
