# Unitflow Technical Debt

## Purpose

This document tracks known technical debt items that were intentionally deferred during the phased implementation.

These items are not bugs. They are design or implementation choices that were acceptable for internal development but should be addressed before broader release, distributed execution, or long-term maintenance.

## Priority: Before Public Release

### 1. `default_resolver` Is A Global Mutable Singleton

**Location:** `unitflow/core/display.py`

The `DisplayResolver` instance used for default display formatting is a module-level mutable singleton populated at import time by the SI and mechanical catalogs.

**Risk:**
- display behavior depends on import order
- tests that register units in the resolver are not isolated from each other
- user-defined units registered in the default resolver mutate shared global state
- incompatible with distributed execution where each worker may have different import state

**Recommended fix:**
- make the resolver a context variable or explicitly passed dependency
- provide a convenience default that can be replaced or scoped per context

**Tracked since:** Phase 5

---

### 2. Serialization Format Has No Version Marker

**Location:** `unitflow/serialization/`

Serialized dicts have no `version` or `schema` field. If the internal representation changes, old serialized data will silently fail to deserialize or deserialize incorrectly.

**Risk:**
- silent data corruption when format evolves
- no way to migrate old serialized models
- dangerous for digital twin and distributed workflows where persistence matters

**Recommended fix:**
- add a `"schema_version": 1` field to all top-level serialized objects
- add version-aware deserialization with clear error on unknown versions

**Tracked since:** Phase 7

---

### 3. `Expr.__hash__` Uses `id(self)`

**Location:** `unitflow/expr/expressions.py`

The base `Expr` class hashes by object identity. Two structurally identical expressions created independently will have different hashes.

**Risk:**
- expressions cannot be used as dict keys or set members meaningfully
- caching or deduplication of equivalent expressions is impossible

**Note:** `Symbol.__hash__` correctly uses structural fields. Only composite expressions (`AddExpr`, `MulExpr`, etc.) are affected.

**Recommended fix:**
- implement structural hashing for composite expression nodes
- ensure hash consistency with `is_same` structural equality

**Tracked since:** Phase 6

---

### 4. `is_same` Method Is Fragile For Non-Dataclass Subclasses

**Location:** `unitflow/expr/expressions.py`, `unitflow/expr/constraints.py`

The `is_same` method on `Expr` and `Constraint` relies on `hasattr(self, "__dataclass_fields__")` to determine how to compare fields. If anyone subclasses `Expr` or `Constraint` without using `@dataclass`, `is_same` falls back to identity comparison, which is silently wrong.

**Risk:**
- silent incorrect structural comparison for custom expression or constraint subclasses
- hard to debug when it fails

**Recommended fix:**
- define an explicit abstract method or protocol for structural comparison
- do not rely on dataclass internals for correctness

**Tracked since:** Phase 6

---

## Priority: Before Distributed Execution

### 5. `UnitNamespace.__getattr__` May Interfere With Pickling

**Location:** `unitflow/define/namespaces.py`

`__getattr__` is guarded against `_`-prefixed names, but pickling and deepcopy protocols may still encounter edge cases depending on the serialization backend.

**Risk:**
- potential infinite recursion or `AttributeError` during pickle/deepcopy if `__dict__` is not yet populated

**Recommended fix:**
- test pickling and deepcopy of `UnitNamespace` explicitly
- add `__getstate__` / `__setstate__` if needed

**Tracked since:** Phase 4

---

### 6. `with_metadata` Sentinel Pattern

**Location:** `unitflow/core/units.py`

The `_UNSET` sentinel is defined at module level and used in `with_metadata(...)` to distinguish "not provided" from `None`. This works but the typing is awkward (`str | None | object`) and requires `# type: ignore` comments.

**Risk:**
- type checker noise
- confusing for contributors unfamiliar with the sentinel pattern

**Recommended fix:**
- consider using a typed sentinel from a utility module
- or accept the current pattern and document it for contributors

**Tracked since:** Phase 5

---

## Priority: Nice To Have

### 7. `__array_function__` Dispatch Path Confidence

**Location:** `unitflow/backends/numpy.py`, `unitflow/core/quantities.py`

NumPy's `__array_function__` protocol may or may not be invoked for `np.sum(Quantity(...))` depending on NumPy version and whether the quantity is recognized as array-like. The current implementation works in tests, but the dispatch path should be verified under different NumPy versions.

**Risk:**
- reductions may silently fall through to `__array_ufunc__` reduce path instead of `__array_function__`
- behavior may change across NumPy major versions

**Recommended fix:**
- add explicit version-gated tests
- verify which dispatch path is actually taken for `np.sum`, `np.mean`

**Tracked since:** Phase 8

---

### 8. No `__abs__` On `Quantity`

**Location:** `unitflow/core/quantities.py`

`abs(quantity)` is not implemented. `__neg__` was added but `__abs__` was not.

**Recommended fix:**
- add `__abs__` returning `Quantity(abs(self.magnitude), self.unit)`

**Tracked since:** Final review

---

### 9. Display Resolver Symbol Propagation In Unit Algebra

**Location:** `unitflow/core/units.py`

`__mul__`, `__truediv__`, and `__pow__` on `Unit` all propagate composed symbols (like `m*s`, `m/s`, `m^2`). This is useful for display but means `.symbol` on composite units contains operator characters that the display resolver also uses as signals for "authored vs composite" decisions.

**Risk:**
- the display resolver's `_should_preserve_authored_unit` heuristic checks for `*` and `/` in symbols to decide whether a unit was "authored" or "computed"
- this coupling is fragile if symbol formatting conventions change

**Recommended fix:**
- consider separating "authored symbol" from "computed display symbol" more explicitly
- or add a flag to `Unit` indicating whether the symbol was user-authored vs auto-generated

**Tracked since:** Phase 5

---

## Summary

| # | Item | Priority | Phase |
|---|------|----------|-------|
| 1 | Global mutable `default_resolver` | Before public release | 5 |
| 2 | Serialization version marker | Before public release | 7 |
| 3 | `Expr.__hash__` id-based | Before public release | 6 |
| 4 | `is_same` fragility | Before public release | 6 |
| 5 | `UnitNamespace` pickling | Before distributed execution | 4 |
| 6 | `with_metadata` sentinel typing | Before distributed execution | 5 |
| 7 | `__array_function__` dispatch confidence | Nice to have | 8 |
| 8 | No `__abs__` on `Quantity` | Nice to have | Final |
| 9 | Symbol propagation coupling | Nice to have | 5 |
