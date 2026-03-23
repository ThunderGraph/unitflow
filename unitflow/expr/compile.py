"""Compile unitflow expression trees into fast numeric callables.

The compiled functions operate on bare floats with all unit overhead
(conversion factors, constant quantities) baked in at compile time.
They are suitable for inner loops of numeric solvers like scipy.optimize.root.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from unitflow.core.units import Unit
from unitflow.expr.constraints import Equation
from unitflow.expr.errors import CompilationError
from unitflow.expr.expressions import (
    AddExpr,
    ConversionExpr,
    DivExpr,
    Expr,
    MulExpr,
    PowExpr,
    QuantityExpr,
    SubExpr,
)
from unitflow.expr.symbols import Symbol


def compile_numeric(
    expr: Expr,
    symbols: Sequence[Symbol],
    reference_units: dict[Symbol, Unit],
) -> Callable[..., float]:
    """Compile an expression into a fast float function.

    The returned callable takes one positional float argument per symbol
    (in the order given by ``symbols``) and returns a float.

    All unit conversions and constant quantities are baked into the
    generated function at compile time so the inner loop is pure arithmetic.

    Args:
        expr: The expression to compile.
        symbols: Ordered list of symbols that become positional arguments.
        reference_units: The unit each symbol's float value is expressed in.

    Raises:
        CompilationError: If a symbol in the expression is not in ``symbols``,
            or if dimensional validation fails.
    """
    _validate_symbols(expr, symbols, reference_units)
    arg_names = [f"x{i}" for i in range(len(symbols))]
    sym_to_arg = {id(sym): arg_names[i] for i, sym in enumerate(symbols)}
    constants: dict[str, float] = {}
    body = _emit_expr(expr, sym_to_arg, reference_units, constants)
    return _build_function("compiled_expr", arg_names, body, constants)


def compile_residual(
    equation: Equation,
    symbols: Sequence[Symbol],
    reference_units: dict[Symbol, Unit],
) -> Callable[..., float]:
    """Compile an Equation into a residual function (lhs - rhs).

    The returned callable takes one positional float argument per symbol
    and returns ``lhs - rhs`` as a float. This is the standard form for
    scipy.optimize.root and similar solvers.

    Args:
        equation: The equation to compile as a residual.
        symbols: Ordered list of symbols that become positional arguments.
        reference_units: The unit each symbol's float value is expressed in.

    Raises:
        CompilationError: If a symbol in the equation is not in ``symbols``,
            or if dimensional validation fails.
    """
    if not isinstance(equation, Equation):
        raise CompilationError("compile_residual expects an Equation.")
    _validate_symbols(equation.left, symbols, reference_units)
    _validate_symbols(equation.right, symbols, reference_units)
    arg_names = [f"x{i}" for i in range(len(symbols))]
    sym_to_arg = {id(sym): arg_names[i] for i, sym in enumerate(symbols)}
    constants: dict[str, float] = {}
    lhs_body = _emit_expr(equation.left, sym_to_arg, reference_units, constants)
    rhs_body = _emit_expr(equation.right, sym_to_arg, reference_units, constants)
    body = f"({lhs_body}) - ({rhs_body})"
    return _build_function("compiled_residual", arg_names, body, constants)


def _validate_symbols(
    expr: Expr,
    symbols: Sequence[Symbol],
    reference_units: dict[Symbol, Unit],
) -> None:
    sym_ids = {id(s) for s in symbols}
    for sym in expr.free_symbols:
        if id(sym) not in sym_ids:
            raise CompilationError(
                f"Symbol '{sym.name}' appears in the expression but is not in the symbols list."
            )
        if sym not in reference_units:
            found = False
            for key in reference_units:
                if key is sym:
                    found = True
                    break
            if not found:
                raise CompilationError(
                    f"Symbol '{sym.name}' has no reference unit in reference_units."
                )


def _emit_expr(
    node: Expr,
    sym_to_arg: dict[int, str],
    reference_units: dict[Symbol, Unit],
    constants: dict[str, float],
) -> str:
    if isinstance(node, Symbol):
        return sym_to_arg[id(node)]

    if isinstance(node, QuantityExpr):
        const_name = f"_c{len(constants)}"
        constants[const_name] = float(node.value.magnitude) * node.value.unit.scale.as_float()
        return const_name

    if isinstance(node, AddExpr):
        left = _emit_expr(node.left, sym_to_arg, reference_units, constants)
        right = _emit_expr(node.right, sym_to_arg, reference_units, constants)
        return f"({left} + {right})"

    if isinstance(node, SubExpr):
        left = _emit_expr(node.left, sym_to_arg, reference_units, constants)
        right = _emit_expr(node.right, sym_to_arg, reference_units, constants)
        return f"({left} - {right})"

    if isinstance(node, MulExpr):
        left = _emit_expr(node.left, sym_to_arg, reference_units, constants)
        right = _emit_expr(node.right, sym_to_arg, reference_units, constants)
        return f"({left} * {right})"

    if isinstance(node, DivExpr):
        left = _emit_expr(node.left, sym_to_arg, reference_units, constants)
        right = _emit_expr(node.right, sym_to_arg, reference_units, constants)
        return f"({left} / {right})"

    if isinstance(node, PowExpr):
        base = _emit_expr(node.base, sym_to_arg, reference_units, constants)
        return f"({base} ** {node.power})"

    if isinstance(node, ConversionExpr):
        inner = _emit_expr(node.expr, sym_to_arg, reference_units, constants)
        inner_dim = node.expr.dimension
        target_dim = node.target_unit.dimension
        if inner_dim != target_dim:
            raise CompilationError(
                f"ConversionExpr dimension mismatch: {inner_dim!r} vs {target_dim!r}"
            )
        inner_unit = _infer_unit(node.expr, reference_units)
        if inner_unit is not None:
            conv_scale = inner_unit.conversion_factor_to(node.target_unit)
            factor_name = f"_c{len(constants)}"
            constants[factor_name] = conv_scale.as_float()
            return f"({inner} * {factor_name})"
        return inner

    raise CompilationError(f"Unsupported expression node type: {type(node).__name__}")


def _infer_unit(node: Expr, reference_units: dict[Symbol, Unit]) -> Unit | None:
    """Best-effort inference of the concrete unit for a sub-expression.

    Returns the reference unit for symbols, the declared unit for constants,
    and composes units for arithmetic nodes. Returns None if inference fails.
    """
    if isinstance(node, Symbol):
        for key in reference_units:
            if key is node:
                return reference_units[key]
        return node.unit

    if isinstance(node, QuantityExpr):
        return node.value.unit

    if isinstance(node, (AddExpr, SubExpr)):
        return _infer_unit(node.left, reference_units)

    if isinstance(node, MulExpr):
        left_u = _infer_unit(node.left, reference_units)
        right_u = _infer_unit(node.right, reference_units)
        if left_u is not None and right_u is not None:
            return left_u * right_u
        return None

    if isinstance(node, DivExpr):
        left_u = _infer_unit(node.left, reference_units)
        right_u = _infer_unit(node.right, reference_units)
        if left_u is not None and right_u is not None:
            return left_u / right_u
        return None

    if isinstance(node, PowExpr):
        base_u = _infer_unit(node.base, reference_units)
        if base_u is not None:
            return base_u ** node.power
        return None

    if isinstance(node, ConversionExpr):
        return node.target_unit

    return None


def _build_function(
    name: str,
    arg_names: list[str],
    body: str,
    constants: dict[str, float],
) -> Callable[..., float]:
    args_str = ", ".join(arg_names)
    source = f"def {name}({args_str}):\n    return {body}\n"
    code = compile(source, f"<unitflow.expr.compile:{name}>", "exec")
    namespace: dict[str, object] = dict(constants)
    exec(code, namespace)
    fn = namespace[name]
    if not callable(fn):
        raise CompilationError("Generated function is not callable.")
    return fn  # type: ignore[return-value]
