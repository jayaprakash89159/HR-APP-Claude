import ast
import operator
from decimal import Decimal


class UnsafeFormulaError(ValueError):
    pass


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
_FUNCTIONS = {'abs': abs, 'min': min, 'max': max, 'round': round}


def evaluate_formula(expression, context):
    """Evaluate arithmetic-only formulas; never executes arbitrary Python."""
    if not expression or len(expression) > 200:
        raise UnsafeFormulaError('Formula is empty or too long.')
    tree = ast.parse(expression, mode='eval')
    return _evaluate(tree.body, context)


def _evaluate(node, context):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))
    if isinstance(node, ast.Name) and node.id in context:
        return Decimal(str(context[node.id]))
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left = _evaluate(node.left, context)
        right = _evaluate(node.right, context)
        if isinstance(node.op, ast.Pow) and abs(right) > 6:
            raise UnsafeFormulaError('Exponent is too large.')
        return _OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.operand, context))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
        return _FUNCTIONS[node.func.id](*[_evaluate(arg, context) for arg in node.args])
    raise UnsafeFormulaError('Only arithmetic, approved variables, and basic numeric functions are allowed.')