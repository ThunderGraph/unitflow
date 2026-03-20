# Contributing to UnitFlow

Thank you for your interest in contributing to UnitFlow. This document covers the expectations and practices for contributing to the project.

## Code of Conduct

Be respectful, constructive, and professional. Engineering is a collaborative discipline and this project reflects that.

## Getting Started

1. Fork the repository and clone your fork.
2. Install development dependencies:

```bash
uv sync
```

3. Run the test suite to confirm your environment is working:

```bash
uv run pytest tests/ -v
```

4. Create a feature branch from `main`:

```bash
git checkout -b feature/your-feature-name
```

## Development Expectations

### Code Quality

- Follow existing code style and conventions. The codebase uses type annotations throughout.
- Keep functions focused. Each function should do one thing.
- Prefer immutable data structures where possible.
- Do not introduce new dependencies without discussion.
- NumPy remains an optional dependency. The semantic core must import and run without it.

### Testing

- All new functionality must include tests.
- Unit tests go in `tests/unit/` under the appropriate subpackage.
- Integration tests go in `tests/integration/`.
- System-level examples go in `tests/system/`.
- Run the full suite before submitting:

```bash
uv run pytest tests/ -v
```

- Tests should be written in pytest style (plain functions, not unittest classes).
- Use descriptive test names that explain what behavior is being verified.

### Commits

- Write clear, concise commit messages.
- Each commit should represent a single logical change.
- Do not bundle unrelated changes in one commit.

### Pull Requests

- Keep pull requests focused on a single concern.
- Describe what your PR does and why.
- Reference any related issues.
- Ensure all tests pass before requesting review.
- Be prepared to respond to feedback and iterate.

## Architecture Guidelines

UnitFlow is built in clean layers with strict dependency rules:

- `core` owns the semantic model (dimensions, scales, units, quantities).
- `expr` owns symbolic expressions and constraints.
- `define` owns extensibility primitives (unit definitions, namespaces, registries, prefix generation).
- `catalogs` ships curated unit packs.
- `serialization` handles structural serialization for all core objects.
- `backends` contains optional integration layers (e.g. NumPy).

Dependencies flow downward only:

- `Dimension` must not depend on `Unit`.
- `Unit` may depend on `Dimension`.
- `Quantity` may depend on `Unit`.
- `Expr` and `Constraint` may depend on `Quantity`, `Unit`, and `Dimension`.
- Catalogs may depend on the semantic core but not on expression or backend layers.
- Backends depend on the semantic core, not the other way around.

If your contribution changes the dependency direction between layers, it will not be accepted without a thorough design discussion first.

## Adding New Units

To add new units to an existing catalog:

1. Define the unit using `define_unit()` with keyword arguments.
2. Use exact `int` or `Fraction` magnitudes. Do not use `float` in unit definitions.
3. Register the unit in the appropriate namespace.
4. Add tests verifying the unit's semantic correctness and conversion factors.

To add SI prefix variants, use `generate_prefixes()` rather than hand-coding each one.

## Adding New Catalogs

New domain catalogs (e.g. `electrical`, `thermal`, `fluids`) are welcome. Each catalog should:

1. Live in `unitflow/catalogs/` as a separate module.
2. Define a `UnitNamespace` for the domain.
3. Use only exact definitions.
4. Include tests in `tests/unit/catalogs/`.
5. Be re-exported through `unitflow/catalogs/__init__.py`.

## Reporting Issues

When reporting a bug:

- Include a minimal reproducible example.
- State what you expected to happen and what actually happened.
- Include the Python version and UnitFlow version.

When requesting a feature:

- Describe the use case, not just the desired API.
- Explain which engineering domain or workflow would benefit.

## License

By contributing to UnitFlow, you agree that your contributions will be licensed under the Apache 2.0 License.
