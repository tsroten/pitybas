# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
import math
import random
import string
import time
from functools import reduce
from typing import Any, Optional, Tuple as _Tuple, Type

from .common import Pri, ExecutionError, StopError, ReturnError
from .expression import Tuple, Expression, Arguments, ListExpr, MatrixExpr
from .graph import MAX_COL, MAX_ROW, PIXEL_COLS, PIXEL_ROWS, TEXT_MAX_ROW
from .token_core import (
    Function,
    InvalidOperation,
    Parent,  # noqa: F401  re-exported as part of this module's public API
    Stub,
    StubToken,
    Token,
    Variable,
    get,
)

# helpers


def add_class(name, *args, **kwargs):
    globals()[name] = type(name, args, kwargs)


# variables


class EOF(Token, Stub):
    def run(self, vm):
        raise StopError


class Const(Variable, Stub):
    value: Any = None

    def set(self, vm, value):
        raise InvalidOperation

    def get(self, vm):
        return self.value


class Value(Const, Stub):
    def __init__(self, value):
        self.value = value
        Variable.__init__(self)

    def get(self, vm):
        return self.value

    def __repr__(self):
        return repr(self.value)


# list/matrix


class List(Variable, Stub):
    absorbs = (Arguments,)

    def __init__(self, name=None):
        self.name = name
        super(List, self).__init__()

    def dim(self, vm, value=None):
        if value is not None:
            assert isinstance(value, int)

            try:
                l = vm.get_list(self.name)
            except KeyError:
                l = []

            l = l[:value] + ([0] * (value - len(l)))
            vm.set_list(self.name, l)
        else:
            return len(vm.get(self))

    def get(self, vm):
        if self.arg:
            arg = vm.get(self.arg)[0]
            assert isinstance(arg, int)
            return vm.get_list(self.name)[arg - 1]

        return vm.get_list(self.name)

    def set(self, vm, value):
        if self.arg:
            arg = vm.get(self.arg)[0]
            assert isinstance(arg, int)
            assert isinstance(value, (int, float, complex))

            l = vm.get_list(self.name)
            i = arg - 1

            # real hardware auto-pads a list with 0s when storing beyond
            # its current dimension; only an in-bounds index is a plain
            # replace
            if i >= len(l):
                l += [0] * (i - len(l) + 1)
            l[i] = value
            vm.set_list(self.name, l)
        else:
            assert isinstance(value, list)
            vm.set_list(self.name, value[:])

        return value

    def __repr__(self):
        if self.arg:
            return "l%s(%s)" % (self.name, self.arg)

        return "l%s" % self.name


class ListToken(List):
    token = "∟"


class Matrix(Variable, Stub):
    absorbs = (Arguments,)

    def __init__(self, name=None):
        self.name = name

    def dim(self, vm, value=None):
        if value is not None:
            assert isinstance(value, list) and len(value) == 2

            a, b = value
            try:
                m = vm.get_matrix(self.name)
            except KeyError:
                m = [[]]

            m = m[:a]
            for i in range(len(m), a):
                n = [0] * b
                m.append(n)

            m = [l[:b] + ([0] * (b - len(l))) for l in m]
            vm.set_matrix(self.name, m)
        else:
            val = vm.get_matrix(self.name)
            return [len(val), len(val[0])]

    def get(self, vm):
        if self.arg:
            arg = vm.get(self.arg)
            assert isinstance(arg, list) and len(arg) == 2
            return vm.get_matrix(self.name)[arg[0] - 1][arg[1] - 1]

        return vm.get_matrix(self.name)

    def set(self, vm, value):
        if self.arg:
            arg = vm.get(self.arg)
            assert isinstance(arg, list) and len(arg) == 2
            assert isinstance(value, (int, float, complex))

            m = vm.get_matrix(self.name)
            m[arg[0] - 1][arg[1] - 1] = value
        else:
            assert isinstance(value, list)
            vm.set_matrix(self.name, value)

        return value

    def __repr__(self):
        return "[%s]" % self.name


class dim(Function):
    def get(self, vm):
        assert self.arg and len(self.arg) == 1

        arg = self.arg.contents[0].flatten()
        assert isinstance(arg, (List, Matrix))
        return arg.dim(vm)

    def set(self, vm, value):
        assert self.arg and len(self.arg) == 1

        arg = self.arg.contents[0].flatten()
        assert isinstance(arg, (List, Matrix))

        arg.dim(vm, value)
        return value


class augment(Function):
    def get(self, vm):
        assert self.arg and len(self.arg) == 2
        a = self.arg.contents[0].flatten()
        b = self.arg.contents[1].flatten()
        if isinstance(a, (List, ListExpr)) and isinstance(b, (List, ListExpr)):
            return vm.get(a) + vm.get(b)
        elif isinstance(a, (Matrix, MatrixExpr)) and isinstance(
            b, (Matrix, MatrixExpr)
        ):
            a = vm.get(a)
            b = vm.get(b)
            assert len(a) == len(b)
            return [left + b[i] for i, left in enumerate(a)]
        else:
            raise ExecutionError("augment() requires List, List or Matrix, Matrix")


class Fill(Function):
    def run(self, vm):
        assert self.arg and len(self.arg) == 2
        num, var = self.arg.contents
        var = var.flatten()
        num = vm.get(num)

        assert isinstance(num, (int, float, complex))
        assert isinstance(var, (List, Matrix))

        if isinstance(var, List):
            l = [num for i in range(len(vm.get(var)))]
            var.set(vm, l)
        elif isinstance(var, Matrix):
            m = []
            o = vm.get(var)
            for a in o:
                c = []
                for b in a:
                    c.append(num)

                m.append(c)

            var.set(vm, m)


class seq(Function):
    def get(self, vm):
        assert self.arg and len(self.arg) in (4, 5)
        arg = self.arg.contents
        expr = arg[0]
        var = arg[1].flatten()
        assert isinstance(var, Variable)
        assert isinstance(expr, Expression)
        step = 1
        if len(arg) == 5:
            step = vm.get(arg[4])
        out = []
        start, end = vm.get(arg[2]), vm.get(arg[3])
        for i in range(start, end + 1, step):
            vm.set_var(var.token, i)
            out.append(vm.get(expr))
        return out


class Sum(Function):
    token = "sum"

    def get(self, vm):
        assert self.arg and len(self.arg) == 1
        arg = self.arg.flatten()
        return sum(vm.get(arg))


class prod(Function):
    def call(self, vm, args):
        assert len(args) in (1, 2, 3)
        lst = args[0]
        assert isinstance(lst, list)

        start = args[1] if len(args) >= 2 else 1
        end = args[2] if len(args) >= 3 else len(lst)
        assert start >= 1 and start <= end <= len(lst)

        return reduce(lambda a, b: a * b, lst[start - 1 : end], 1)


class DeltaList(Function):
    token = "ΔList"

    def get(self, vm):
        assert self.arg and len(self.arg) == 1
        lst = vm.get(self.arg.flatten())
        return [lst[i + 1] - lst[i] for i in range(len(lst) - 1)]


class cumSum(Function):
    def get(self, vm):
        assert self.arg and len(self.arg) == 1
        lst = vm.get(self.arg.flatten())
        total = 0
        out = []
        for x in lst:
            total += x
            out.append(total)
        return out


class SortA(Function):
    descending = False

    def run(self, vm):
        assert self.arg and len(self.arg) >= 1
        lists = [c.flatten() for c in self.arg.contents]
        assert all(isinstance(l, List) for l in lists)
        key = vm.get_list(lists[0].name)
        indices = sorted(range(len(key)), key=lambda i: key[i], reverse=self.descending)
        vm.set_list(lists[0].name, [key[i] for i in indices])
        for dep_list in lists[1:]:
            dep = vm.get_list(dep_list.name)
            vm.set_list(dep_list.name, [dep[i] for i in indices])


class SortD(SortA):
    descending = True


class Ans(Const):
    def get(self, vm):
        return vm.get_var("Ans")


class Pi(Const):
    token = "π"
    value = math.pi


class e(Const):
    token = "e"
    value = math.e


class SimpleVar(Variable, Stub):
    def set(self, vm, value):
        return vm.set_var(self.token, value)

    def get(self, vm):
        return vm.get_var(self.token)


class NumVar(SimpleVar, Stub):
    def get(self, vm):
        return vm.get_var(self.token, 0)


class StrVar(SimpleVar, Stub):
    def get(self, vm):
        return vm.get_var(self.token, "")


class Theta(NumVar):
    token = "\u03b8"


class THETA(NumVar):
    def set(self, vm, value):
        return vm.set_var(Theta.token, value)

    def get(self, vm):
        return vm.get_var(Theta.token)


for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    add_class(c, NumVar)

for i in range(10):
    add_class("Str%i" % i, StrVar)


class GraphVar(Variable, Stub):
    graph_attr: Optional[str] = None

    def set(self, vm, value):
        setattr(vm.graph, self.graph_attr, value)

    def get(self, vm):
        return getattr(vm.graph, self.graph_attr)


class Xmin(GraphVar):
    graph_attr = "xmin"


class Xmax(GraphVar):
    graph_attr = "xmax"


class Xscl(GraphVar):
    graph_attr = "xscl"


class Ymin(GraphVar):
    graph_attr = "ymin"


class Ymax(GraphVar):
    graph_attr = "ymax"


class Yscl(GraphVar):
    graph_attr = "yscl"


class DelVar(Token):
    absorbs = (Expression, Variable)

    def run(self, vm):
        arg = self.arg
        if arg is None:
            return
        if isinstance(arg, Expression):
            arg = arg.flatten()
        if isinstance(arg, List):
            vm.lists.pop(arg.name, None)
        elif isinstance(arg, Matrix):
            vm.matrix.pop(arg.name, None)
        else:
            vm.vars.pop(arg.token, None)


class Archive(Token):
    absorbs = (Expression, Variable)

    def run(self, vm):
        pass


class UnArchive(Archive):
    pass


class ClrList(Token):
    absorbs = (Expression, Variable, Tuple)

    def run(self, vm):
        arg = self.arg
        if not arg:
            raise ExecutionError("ClrList used without arguments")

        lists = arg.contents if isinstance(arg, Tuple) else [arg]
        for lst in lists:
            if isinstance(lst, Expression):
                lst = lst.flatten()
            assert isinstance(lst, List)
            lst.dim(vm, 0)


class ClrAllLists(Token):
    def run(self, vm):
        for name in list(vm.lists):
            vm.set_list(name, [])


# operators


class Stor(Token):
    token = "→"
    priority = Pri.SET

    def run(self, vm, left, right):
        ans = vm.get(left)
        right.set(vm, ans)
        return ans


class Store(Stor):
    token = "->"


class Operator(Token, Stub):
    @get
    def run(self, vm, left, right):
        return self.op(left, right)


def round_precision(ans):
    # 14 digits of precision?
    if isinstance(ans, list):
        return [round_precision(a) for a in ans]

    if abs(ans - int(ans)) < 0.00000000000001:
        return int(ans)

    return ans


class FloatOperator(Operator, Stub):
    @get
    def run(self, vm, left, right):
        return round_precision(self.op(left, right))


class AddSub(Operator, Stub):
    priority = Pri.ADDSUB


class MultDiv(FloatOperator, Stub):
    priority = Pri.MULTDIV


class Exponent(Operator, Stub):
    priority = Pri.EXPONENT


class RightExponent(Exponent, Stub):
    def fill_right(self):
        return Value(None)


class Bool(Operator, Stub):
    priority = Pri.BOOL

    @get
    def run(self, vm, left, right):
        return int(bool(self.bool(left, right)))


# a Function expecting a single Expression as the argument
class MathExprFunction(Function, Stub):
    def get(self, vm):
        assert len(self.arg) == 1
        args = vm.get(self.arg)
        return self.call(vm, args[0])


class Logic(Bool):
    priority = Pri.LOGIC


# math


def is_matrix(value):
    return isinstance(value, list) and value and isinstance(value[0], list)


def is_list(value):
    return isinstance(value, list) and not is_matrix(value)


def elementwise(op, left, right):
    """Apply a scalar binary op across List/Matrix operands the way real
    TI-BASIC does: same-shape List/List or Matrix/Matrix pairs combine
    element by element, and a scalar broadcasts against every element of
    a List or Matrix."""
    if isinstance(left, list) and isinstance(right, list):
        if is_matrix(left) and is_matrix(right):
            if len(left) != len(right) or len(left[0]) != len(right[0]):
                raise ExecutionError("ERR:DIM MISMATCH")
            return [[op(a, b) for a, b in zip(ra, rb)] for ra, rb in zip(left, right)]
        elif is_list(left) and is_list(right):
            if len(left) != len(right):
                raise ExecutionError("ERR:DIM MISMATCH")
            return [op(a, b) for a, b in zip(left, right)]
        else:
            raise ExecutionError("ERR:DATA TYPE")
    elif isinstance(left, list):
        if is_matrix(left):
            return [[op(a, right) for a in row] for row in left]
        return [op(a, right) for a in left]
    elif isinstance(right, list):
        if is_matrix(right):
            return [[op(left, b) for b in row] for row in right]
        return [op(left, b) for b in right]
    else:
        return op(left, right)


def matrix_multiply(left, right):
    rows, mid = len(left), len(left[0])
    mid_b, cols = len(right), len(right[0])
    if mid != mid_b:
        raise ExecutionError("ERR:DIM MISMATCH")

    return [
        [sum(left[i][k] * right[k][j] for k in range(mid)) for j in range(cols)]
        for i in range(rows)
    ]


class Plus(AddSub):
    token = "+"

    def op(self, left, right):
        return elementwise(lambda a, b: a + b, left, right)


class Minus(AddSub):
    token = "-"

    def op(self, left, right):
        return elementwise(lambda a, b: a - b, left, right)


class Negate(Token):
    """The real calculator's dedicated negation key (raised minus),
    distinct from the Minus/subtraction token. Unlike '-', it is never
    ambiguous with a binary operator, so Base.append() (expression.py)
    always collapses "Negate X" into "-1 * X" regardless of where it
    appears -- not just when it happens to lead the expression."""

    token = "⁻"
    priority = Pri.NONE


class NegateTilde(Negate):
    """'~' is the plaintext ASCII rendering of the same negation key used
    when a .8xp program is dumped to text (ASCII has no raised-minus glyph),
    so it must behave identically to '⁻' rather than being left unhandled."""

    token = "~"


class Mult(MultDiv):
    token = "*"

    def op(self, left, right):
        # real matrix multiplication, not element-wise, when both sides
        # are matrices; List*List and any scalar broadcast stay element-wise
        if is_matrix(left) and is_matrix(right):
            return matrix_multiply(left, right)

        return elementwise(lambda a, b: a * b, left, right)


class Div(MultDiv):
    token = "/"

    def op(self, left, right):
        if is_matrix(left) and is_matrix(right):
            raise ExecutionError("ERR:DATA TYPE")

        return elementwise(lambda a, b: a / b, left, right)


class Pow(Exponent):
    token = "^"

    def op(self, left, right):
        return left**right


class transpose(RightExponent):
    token = "_T"

    def op(self, left, right):
        vm = {"tmp": left}
        rows, cols = Matrix("tmp").dim(vm)
        out = [[0] * rows for i in range(cols)]
        for y in range(rows):
            for x in range(cols):
                out[x][y] = left[y][x]
        return out


class Square(RightExponent):
    token = "²"

    def op(self, left, right):
        return left**2


class Cube(RightExponent):
    token = "³"

    def op(self, left, right):
        return left**3


class Inverse(RightExponent):
    token = "⁻¹"

    def op(self, left, right):
        return left**-1


class Sqrt(MathExprFunction):
    token = "√"

    def call(self, vm, arg):
        return math.sqrt(arg)


class sqrt(Sqrt):
    pass


class CubeRoot(MathExprFunction):
    token = "³√"

    def call(self, vm, arg):
        # TODO: proper accuracy. maybe write a numpy addon, to increase accuracy
        # if numpy is installed?

        # round to within our accuracy bounds
        # this allows us to reverse a cube properly, as long as we don't pass
        # 14 significant digits
        i = arg ** (1.0 / 3)
        places = 14 - len(str(int(math.floor(i))))
        if places > 0:
            return round(i, places)
        else:
            # oh well
            return i


class NthRoot(Operator):
    priority = Pri.EXPONENT
    token = "×√"

    def op(self, left, right):
        if right < 0 and left % 2 == 0:
            raise ExecutionError("ERR:NONREAL ANS")

        # Compute the real nth root, preserving the sign for odd roots of
        # negative radicands (Python's ** would produce a complex number).
        if right < 0:
            i = -((-right) ** (1.0 / left))
        else:
            i = right ** (1.0 / left)

        # Round to within our accuracy bounds, matching CubeRoot's approach,
        # so that perfect roots (e.g. 3×√1000 = 10) are not returned as
        # floating-point noise (9.999999999999998).
        places = 14 - len(str(int(math.floor(abs(i)))))
        if places > 0:
            return round(i, places)
        return i


class SciNot(Operator):
    priority = Pri.EXPONENT
    token = "ᴇ"

    def fill_left(self):
        return Value(1)

    def op(self, left, right):
        return left * (10**right)


class Abs(MathExprFunction):
    token = "abs"

    def call(self, vm, arg):
        return abs(arg)


class gcd(Function):
    def call(self, vm, args):
        assert len(args) == 1 and isinstance(args[0], list) or len(args) == 2
        if len(args) == 1:
            return reduce(lambda a, b: math.gcd(a, b), args[0])
        else:
            return math.gcd(*args)


class lcm(Function):
    def call(self, vm, args):
        assert len(args) == 2
        a, b = args
        if isinstance(a, list):
            a = self.lcm_list(*a)
        if isinstance(b, list):
            b = self.lcm_list(*b)
        return self.lcm(a, b)

    @staticmethod
    def lcm(a, b):
        return a * b // math.gcd(a, b)

    @classmethod
    def lcm_list(cls, *args):
        args = list(args)
        a = args.pop(0)
        while args:
            b = args.pop(0)
            a = cls.lcm(a, b)
        return a


class Min(Function):
    token = "min"

    def call(self, vm, args):
        assert len(args) == 2
        return min(*args)


class Max(Function):
    token = "max"

    def call(self, vm, args):
        assert len(args) in (1, 2)
        if len(args) == 1:
            assert isinstance(args[0], list)
            return max(args[0])
        else:
            a1, a2 = args
            if not isinstance(a1, list):
                a1 = [a1]
            if not isinstance(a2, list):
                a2 = [a2]
            return max(a1 + a2)


class Round(Function):
    token = "round"

    def call(self, vm, args):
        assert len(args) in (1, 2)

        if len(args) == 2:
            places = args[1]
        else:
            places = 9

        return round(args[0], places)


class Int(MathExprFunction):
    token = "int"

    def call(self, vm, arg):
        return math.floor(arg)


class iPart(MathExprFunction):
    def call(self, vm, arg):
        return int(arg)


class fPart(MathExprFunction):
    def call(self, vm, arg):
        return math.modf(arg)[0]


class floor(MathExprFunction):
    def call(self, vm, arg):
        return math.floor(arg)


class ceiling(MathExprFunction):
    def call(self, vm, arg):
        return math.ceil(arg)


class mod(Function):
    def call(self, vm, args):
        assert len(args) == 2
        return args[0] % args[1]


class expr(MathExprFunction):
    def call(self, vm, arg):
        from .parse import Parser

        return Parser.parse_line(vm, arg)


# trig


class sin(MathExprFunction):
    def call(self, vm, arg):
        if vm.degree_mode:
            arg = math.radians(arg)
        return math.sin(arg)


class cos(MathExprFunction):
    def call(self, vm, arg):
        if vm.degree_mode:
            arg = math.radians(arg)
        return math.cos(arg)


class tan(MathExprFunction):
    def call(self, vm, arg):
        if vm.degree_mode:
            arg = math.radians(arg)
        return math.tan(arg)


# TODO: subclass these inverse functions with the unicode -1 token, and
# probably add support for that in the parser for ints too
class asin(MathExprFunction):
    token = "sin-1"

    def call(self, vm, arg):
        result = math.asin(arg)
        return math.degrees(result) if vm.degree_mode else result


class acos(MathExprFunction):
    token = "cos-1"

    def call(self, vm, arg):
        result = math.acos(arg)
        return math.degrees(result) if vm.degree_mode else result


class atan(MathExprFunction):
    token = "tan-1"

    def call(self, vm, arg):
        result = math.atan(arg)
        return math.degrees(result) if vm.degree_mode else result


# angle mode


def _terminal(right):
    # RightExponent.fill_right() pads a trailing Value(None) onto a
    # postfix operator with nothing after it; that's how we tell "D°" (no
    # minutes follow) apart from "D°M" (mid-DMS-chain, more to fold in).
    return isinstance(right, Value) and right.value is None


class DegreeSymbol(RightExponent):
    # postfix °: treats its operand as degrees regardless of the current
    # angle mode, converting to radians only if we're in Radian mode
    # (in Degree mode it's a no-op since raw numbers are already degrees).
    # Also doubles as the D in a D°M'S" DMS literal - when a minutes value
    # follows, fold it in and defer the mode conversion to whichever
    # symbol (this one, ', or ") turns out to be last in the chain.
    token = "\xb0"

    def run(self, vm, left, right):
        value = vm.get(left)
        if _terminal(right):
            return value if vm.degree_mode else math.radians(value)

        sign = -1 if value < 0 else 1
        return value + sign * vm.get(right) / 60


class MinuteSymbol(RightExponent):
    # postfix ': only meaningful as the M in a DMS literal (D°M'S" or
    # D°M'). Folds in a following seconds value, deferring the mode
    # conversion to " if present, or applies it here if seconds are absent.
    token = "'"

    def run(self, vm, left, right):
        value = vm.get(left)
        if _terminal(right):
            return value if vm.degree_mode else math.radians(value)

        sign = -1 if value < 0 else 1
        return value + sign * vm.get(right) / 3600


class SecondSymbol(RightExponent):
    # postfix ": the S in a DMS literal (D°M'S"). Always the last
    # component - nothing can follow seconds - so always applies the
    # degree/radian mode conversion.
    token = '"'

    def run(self, vm, left, right):
        value = vm.get(left)
        return value if vm.degree_mode else math.radians(value)


class RadianSymbol(RightExponent):
    # postfix r: the mirror image of ° - treats its operand as radians
    # regardless of the current angle mode
    token = "r"

    def run(self, vm, left, right):
        value = vm.get(left)
        return math.degrees(value) if vm.degree_mode else value


class sinh(MathExprFunction):
    def call(self, vm, arg):
        return math.sinh(arg)


class cosh(MathExprFunction):
    def call(self, vm, arg):
        return math.cosh(arg)


class tanh(MathExprFunction):
    def call(self, vm, arg):
        return math.tanh(arg)


class asinh(MathExprFunction):
    token = "sinh-1"

    def call(self, vm, arg):
        return math.asinh(arg)


class acosh(MathExprFunction):
    token = "cosh-1"

    def call(self, vm, arg):
        return math.acosh(arg)


class atanh(MathExprFunction):
    token = "tanh-1"

    def call(self, vm, arg):
        return math.atanh(arg)


# probability


class nPr(Operator):
    # TODO: nPr and nCr should support lists
    priority = Pri.PROB

    def op(self, left, right):
        return math.factorial(left) // math.factorial((left - right))


class nCr(Operator):
    priority = Pri.PROB

    def op(self, left, right):
        return math.factorial(left) // (
            math.factorial(right) * math.factorial((left - right))
        )


class Factorial(Exponent):
    token = "!"

    def op(self, left, right):
        return math.factorial(left)

    def fill_right(self):
        return Value(None)


# random numbers


class rand(Variable):
    def get(self, vm):
        return random.random()

    def set(self, vm, value):
        random.seed(value)


# rand is defined twice: once as a Variable (bare `rand` returns a random
# number) and once as a Function (`rand(n)` returns a list of n random numbers).
# Both definitions are intentional — each registers under a different base class
# in the token registry via the Tracker metaclass, so both are reachable at
# runtime even though the module-level name only holds the second definition.
class rand(Function):  # type: ignore[no-redef]  # noqa: F811
    def call(self, vm, args):
        assert len(args) == 1
        return [random.random() for i in range(args[0])]


class randInt(Function):
    def call(self, vm, args):
        assert len(args) in (2, 3)

        if args[0] > args[1]:
            args[0], args[1] = args[1], args[0]

        if len(args) == 2:
            return random.randint(*args)

        return [random.randint(*args[:2]) for i in range(args[2])]


class randNorm(Function):
    def call(self, vm, args):
        assert len(args) in (2, 3)

        if len(args) == 3:
            args, n = args[:2], args[2]
        else:
            n = 1

        return [random.normalvariate(*args) for i in range(n)]


class randBin(Function):
    def call(self, vm, args):
        # numpy.random has a binomial distribution, or I could write my own...
        raise NotImplementedError


class randM(Function):
    def call(self, vm, args):
        # I don't know how I'm going to do lists and matrices yet
        raise NotImplementedError


# boolean


class And(Bool):
    token = "and"

    def bool(self, left, right):
        return left and right


class Or(Bool):
    token = "or"

    def bool(self, left, right):
        return left or right


class xor(Bool):
    def bool(self, left, right):
        return left ^ right


class Not(Function):
    token = "not"

    def get(self, vm):
        args = vm.get(self.arg)
        assert len(args) == 1

        return int(bool(not args[0]))


# logic


class Equals(Logic):
    token = "="

    def bool(self, left, right):
        return left == right


class NotEquals(Logic):
    token = "~="

    def bool(self, left, right):
        return left != right


class NotEqualsToken(NotEquals):
    token = "≠"


class LessThan(Logic):
    token = "<"

    def bool(self, left, right):
        return left < right


class GreaterThan(Logic):
    token = ">"

    def bool(self, left, right):
        return left > right


class LessOrEquals(Logic):
    token = "<="

    def bool(self, left, right):
        return left <= right


class LessOrEqualsToken(LessOrEquals):
    token = "≤"


class GreaterOrEquals(Logic):
    token = ">="

    def bool(self, left, right):
        return left >= right


class GreaterOrEqualsToken(GreaterOrEquals):
    token = "≥"


# string manipulation


class inString(Function):
    def call(self, vm, args):
        assert len(args) == 2 or len(args) == 3 and isinstance(args[2], int)
        assert isinstance(args[0], str) and isinstance(args[1], str)
        haystack = args[0]
        needle = args[1]
        # TI's start arg is 1-based; str.find is 0-based (default 0 == start 1).
        skip = 0
        if len(args) == 3:
            skip = args[2] - 1
        pos = haystack.find(needle, skip)
        # TI returns a 1-based position, or 0 when not found (str.find gives -1).
        return pos + 1


class sub(Function):
    def call(self, vm, args):
        assert len(args) == 3
        s = args[0]
        a, b = args[1], args[2]
        assert a > 0 and b < len(s)
        return s[a - 1 : a - 1 + b]


class length(Function):
    def call(self, vm, args):
        assert len(args) == 1
        return len(args[0])


class toString(MathExprFunction):
    def call(self, vm, arg):
        if isinstance(arg, str):
            raise ExecutionError("ERR:DATA TYPE")
        return str(vm.disp_round(arg))


# control flow


class Block(StubToken):
    absorbs: _Tuple[Type[Any], ...] = (Expression, Value)

    def find_end(self, vm, or_else=False, cur=False):
        tokens = vm.find(Block, Then, Else, End, wrap=False)
        blocks = []
        thens = 0
        for row, col, token in tokens:
            if not cur and token is self:
                continue

            if isinstance(token, If):
                continue

            if isinstance(token, Then):
                thens += 1
                blocks.append(token)
            elif isinstance(token, Block):
                blocks.append(token)
            elif isinstance(token, End):
                if (thens == 0 or not or_else) and not blocks:
                    return row, col, token
                else:
                    b = blocks.pop(0)
                    if isinstance(b, Then):
                        thens -= 1
            elif or_else and isinstance(token, Else):
                if thens == 0:
                    return row, col, token


class If(Block):
    def run(self, vm):
        if self.arg is None:
            raise ExecutionError("If statement without condition")

        true = bool(vm.get(self.arg))

        cur = vm.cur()
        if isinstance(cur, Then):
            vm.push_block()
            vm.inc()

            if not true:
                end = self.find_end(vm, or_else=True)
                if end:
                    row, col, end = end
                    if isinstance(end, End):
                        vm.pop_block()

                    vm.goto(row, col)
                    vm.inc()
                else:
                    raise StopError("If/Then could not find End on negative expression")
        elif true:
            vm.run(cur)
        else:
            vm.inc_row()

    def resume(self, vm, row, col):
        pass

    def stop(self, vm, row, col):
        pass


class Then(Token):
    def run(self, vm):
        raise ExecutionError("cannot execute a standalone Then statement")


class Else(Token):
    def run(self, vm):
        row, col, block = vm.pop_block()
        assert isinstance(block, If)
        end = block.find_end(vm)
        if end:
            row, col, end = end
        else:
            raise StopError("Else could not find End")

        vm.goto(row, col)
        vm.inc()


class Loop(Block, Stub):
    def run(self, vm):
        if self.arg is None:
            raise ExecutionError("%s statement without condition" % self.token)

        row, col, _ = vm.running[-1]
        self.resume(vm, row, col)

    def loop(self, vm):
        return True

    def resume(self, vm, row, col):
        vm.goto(row, col)
        if self.loop(vm):
            vm.push_block((row, col, self))
            vm.inc()
        else:
            self.stop(vm, row, col)

    def stop(self, vm, row, col):
        vm.goto(row, col)
        end = self.find_end(vm)
        if end:
            row, col, end = end
        else:
            raise StopError("%s could not find End" % self.token)

        vm.goto(row, col)
        vm.inc()


class While(Loop):
    def loop(self, vm):
        return bool(vm.get(self.arg))


class Repeat(Loop):
    def loop(self, vm):
        return not bool(vm.get(self.arg))


class For(Loop, Function):
    pos = None

    def loop(self, vm):
        if len(self.arg) in (3, 4):
            var = self.arg.contents[0]
            args = self.arg.contents[1:]

            if len(args) == 3:
                inc = vm.get(args[2])
                args = args[:2]
            else:
                inc = 1
            forward = inc > 0
            start, end = args

            if self.pos is None:
                self.pos = vm.get(start)
            else:
                self.pos += inc

            var.set(vm, self.pos)
            if (
                forward
                and self.pos > vm.get(end)
                or not forward
                and self.pos < vm.get(end)
            ):
                return False
            else:
                return True
        else:
            raise ExecutionError("incorrect arguments to For loop")

    def stop(self, vm, row, col):
        self.pos = None
        Loop.stop(self, vm, row, col)


class End(Token):
    def run(self, vm):
        try:
            row, col, block = vm.pop_block()
            block.resume(vm, row, col)
        except ExecutionError:
            pass


class Continue(Token):
    def run(self, vm):
        for row, col, block in reversed(vm.blocks):
            if not isinstance(block, If):
                block.resume(vm, row, col)
                break
        else:
            raise ExecutionError("Continue could not find a block to continue")


class Break(Token):
    def run(self, vm):
        for i, (row, col, block) in enumerate(reversed(vm.blocks)):
            if not isinstance(block, If):
                block.stop(vm, row, col)
                vm.blocks = vm.blocks[: -i - 1]
                break
        else:
            raise ExecutionError("Break could not find a block to end")


class Lbl(StubToken):
    absorbs = (Expression, Value)

    @staticmethod
    def guess_label(vm, arg):
        label = None
        if isinstance(arg, Expression):
            arg = arg.flatten()

        if isinstance(arg, Value):
            label = vm.get(arg)
        elif isinstance(arg, Variable):
            label = arg.token
        elif isinstance(arg, Expression):
            # A letter+digit label (e.g. "M1") parses as implied
            # multiplication (Variable * Value), not a single token, so
            # arg.flatten() can't collapse it to one. Value.token is a
            # fixed class-level placeholder ("Value"), not the digit
            # actually parsed, so str(arg.flatten()) would render every
            # such expression identically regardless of the literal.
            # Reconstruct the label from each part's real value instead.
            parts = []
            for token in arg.contents:
                if isinstance(token, Value):
                    parts.append(str(token.value))
                elif isinstance(token, Variable):
                    parts.append(token.token)
            label = "".join(parts)

        return str(label)

    def get_label(self, vm):
        return Lbl.guess_label(vm, self.arg)


class Goto(Token):
    absorbs = (Expression, Value)

    def run(self, vm):
        Goto.goto(vm, self.arg)

    @staticmethod
    def goto(vm, token):
        label = Lbl.guess_label(vm, token)
        if label:
            for row, col, token in vm.find(Lbl, wrap=True):
                if token.get_label(vm) == label:
                    vm.goto(row, col)
                    return

        raise ExecutionError("could not find a label to Goto: %s" % token)


class IsGreaterThanSkip(Function):
    token = "IS>"

    def run(self, vm):
        assert self.arg and len(self.arg) == 2
        var, value = self.arg.contents

        new = vm.get(var) + 1
        var.set(vm, new)

        if new > vm.get(value):
            vm.inc_row()


class DsLessThanSkip(Function):
    token = "DS<"

    def run(self, vm):
        assert self.arg and len(self.arg) == 2
        var, value = self.arg.contents

        new = vm.get(var) - 1
        var.set(vm, new)

        if new < vm.get(value):
            vm.inc_row()


class Menu(Function):
    def run(self, vm):
        args = self.arg.contents[:]
        l = len(args)
        if l >= 3 and (l - 3) % 2 == 0:
            title = args.pop(0)
            descs = args[::2]
            labels = args[1::2]

            # Title/description text is evaluated up front so IO.menu()
            # backends receive plain display strings, matching what a real
            # Menu( shows on-screen. Each label is left as a raw,
            # unevaluated token: Goto.goto() (via Lbl.guess_label) needs
            # its parse-tree shape, not a plain value, to resolve the jump
            # target.
            menu = ((vm.get(title), list(zip(vm.get(*descs), labels))),)

            label = vm.io.menu(menu)
            Goto.goto(vm, label)
        else:
            raise ExecutionError("Invalid arguments to Menu(): %s" % args)


class Pause(Token):
    absorbs = (Expression, Variable)

    def run(self, vm):
        cur = self.arg
        if cur:
            vm.io.pause(vm.get(cur))
        else:
            vm.io.pause()


class Stop(Token):
    def run(self, vm):
        raise StopError


class Return(Token):
    def run(self, vm):
        raise ReturnError


# input/output


class ClrHome(Token):
    def run(self, vm):
        vm.io.clear()


class ClrDraw(Token):
    def run(self, vm):
        vm.graph.clear()
        vm.io.clr_draw()


# Graph DataBase: the window variables that fully describe the current
# viewing window, snapshotted by StoreGDB/RecallGDB. Extend this tuple to
# include equation state once Y1-Y9 equations exist.
GDB_ATTRS = ("xmin", "xmax", "xscl", "ymin", "ymax", "yscl", "axes_on")


def pic_gdb_slot(vm, arg):
    """Evaluate a StorePic/RecallPic/StoreGDB/RecallGDB slot argument.

    Raises ERR:DOMAIN for anything other than an integer 0-9, matching how
    other graph commands (e.g. Text() validate their arguments).
    """
    assert arg is not None
    n = vm.get(arg)

    if not isinstance(n, int) or not (0 <= n <= 9):
        raise ExecutionError("ERR:DOMAIN")

    return n


class StorePic(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        n = pic_gdb_slot(vm, self.arg)
        vm.pics[n] = [row[:] for row in vm.graph.pixels]


class RecallPic(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        n = pic_gdb_slot(vm, self.arg)

        if n in vm.pics:
            vm.graph.pixels = [row[:] for row in vm.pics[n]]
            vm.io.clr_draw()


class StoreGDB(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        n = pic_gdb_slot(vm, self.arg)
        vm.gdbs[n] = {attr: getattr(vm.graph, attr) for attr in GDB_ATTRS}


class RecallGDB(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        n = pic_gdb_slot(vm, self.arg)

        if n in vm.gdbs:
            for attr, value in vm.gdbs[n].items():
                setattr(vm.graph, attr, value)
            vm.io.clr_draw()


class PtFunction(Function, Stub):
    # True to turn the point on, False to turn it off, None to toggle
    on: Optional[bool] = None

    def call(self, vm, args):
        assert len(args) in (2, 3)
        x, y = args[0], args[1]

        pixel = vm.graph.to_pixel(x, y)
        if pixel is None:
            return

        px, py = pixel
        on = self.on if self.on is not None else not vm.graph.get_pixel(px, py)

        vm.graph.set_pixel(px, py, on)
        vm.io.draw_pixel(px, py, on)


class PtOn(PtFunction):
    token = "Pt-On"
    on = True


class PtOff(PtFunction):
    token = "Pt-Off"
    on = False


class PtChange(PtFunction):
    token = "Pt-Change"
    on = None


class PxlFunction(Function, Stub):
    # True to turn the pixel on, False to turn it off, None to toggle
    on: Optional[bool] = None

    def call(self, vm, args):
        assert len(args) == 2
        row, col = round(args[0]), round(args[1])

        if not (0 <= row <= MAX_ROW and 0 <= col <= MAX_COL):
            return

        on = self.on if self.on is not None else not vm.graph.get_pixel(col, row)

        vm.graph.set_pixel(col, row, on)
        self.notify(vm, row, col, on)

    def notify(self, vm, row, col, on):
        raise NotImplementedError


class PxlOn(PxlFunction):
    token = "Pxl-On"
    on = True

    def notify(self, vm, row, col, on):
        vm.io.pxl_on(row, col)


class PxlOff(PxlFunction):
    token = "Pxl-Off"
    on = False

    def notify(self, vm, row, col, on):
        vm.io.pxl_off(row, col)


class PxlChange(PxlFunction):
    token = "Pxl-Change"
    on = None

    def notify(self, vm, row, col, on):
        vm.io.pxl_change(row, col, on)


class PxlTest(Function):
    token = "Pxl-Test"

    def call(self, vm, args):
        assert len(args) == 2
        row, col = round(args[0]), round(args[1])

        if not (0 <= row <= MAX_ROW and 0 <= col <= MAX_COL):
            return 0

        return 1 if vm.graph.get_pixel(col, row) else 0


def _clip_segment(graph, x1, y1, x2, y2):
    """Clip (x1,y1)-(x2,y2) to the graph window (Liang-Barsky).

    Returns the clipped ((x1,y1), (x2,y2)) endpoints, or None if the
    segment lies entirely outside the window.
    """
    if graph.xmax == graph.xmin or graph.ymax == graph.ymin:
        return None

    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0

    for p, q in (
        (-dx, x1 - graph.xmin),
        (dx, graph.xmax - x1),
        (-dy, y1 - graph.ymin),
        (dy, graph.ymax - y1),
    ):
        if p == 0:
            if q < 0:
                return None
            continue

        t = q / p
        if p < 0:
            if t > t1:
                return None
            t0 = max(t0, t)
        else:
            if t < t0:
                return None
            t1 = min(t1, t)

    if t0 > t1:
        return None

    return (x1 + t0 * dx, y1 + t0 * dy), (x1 + t1 * dx, y1 + t1 * dy)


def _plot_line(graph, px1, py1, px2, py2, on):
    """Bresenham a line between two pixel coordinates, setting each pixel."""
    dx = abs(px2 - px1)
    dy = -abs(py2 - py1)
    sx = 1 if px1 < px2 else -1
    sy = 1 if py1 < py2 else -1
    err = dx + dy

    px, py = px1, py1
    while True:
        graph.set_pixel(px, py, on)

        if px == px2 and py == py2:
            break

        e2 = 2 * err
        if e2 >= dy:
            err += dy
            px += sx
        if e2 <= dx:
            err += dx
            py += sy


def draw_line(vm, x1, y1, x2, y2, on=True):
    """Plot a line between two window coordinates, clipping to the window.

    Shared by Line(, Horizontal, and Vertical. Points outside the window
    are silently skipped rather than clamped or raising, consistent with
    GraphState.to_pixel's contract.
    """
    clipped = _clip_segment(vm.graph, x1, y1, x2, y2)
    if clipped is not None:
        p1 = vm.graph.to_pixel(*clipped[0])
        p2 = vm.graph.to_pixel(*clipped[1])
        if p1 is not None and p2 is not None:
            _plot_line(vm.graph, p1[0], p1[1], p2[0], p2[1], on)

    vm.io.draw_line(x1, y1, x2, y2, on)


def draw_circle(vm, x, y, r, on=True):
    """Plot a circle via analytic point generation, skipping off-window points."""
    graph = vm.graph

    if graph.xmax != graph.xmin and graph.ymax != graph.ymin and r != 0:
        px_radius = abs(r) / (graph.xmax - graph.xmin) * MAX_COL
        py_radius = abs(r) / (graph.ymax - graph.ymin) * MAX_ROW
        pixel_radius = max(px_radius, py_radius)

        # a circle rasterized onto the 95x63 grid can never need more points
        # than its bounding-box perimeter to look unbroken, regardless of
        # how large r is in window coordinates
        max_steps = 4 * (PIXEL_COLS + PIXEL_ROWS)
        steps = min(max_steps, max(4, int(2 * math.pi * pixel_radius)))

        seen = set()
        for i in range(steps):
            theta = 2 * math.pi * i / steps
            pixel = graph.to_pixel(x + r * math.cos(theta), y + r * math.sin(theta))
            if pixel is None or pixel in seen:
                continue

            seen.add(pixel)
            graph.set_pixel(pixel[0], pixel[1], on)

    vm.io.draw_circle(x, y, r, on)


class Line(Function):
    def call(self, vm, args):
        assert len(args) in (4, 5)
        x1, y1, x2, y2 = args[0], args[1], args[2], args[3]
        on = args[4] != 0 if len(args) == 5 else True

        draw_line(vm, x1, y1, x2, y2, on)


class Circle(Function):
    def call(self, vm, args):
        assert len(args) == 3
        x, y, r = args

        draw_circle(vm, x, y, r)


class Horizontal(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        assert self.arg is not None
        y = vm.get(self.arg)

        draw_line(vm, vm.graph.xmin, y, vm.graph.xmax, y)


class Vertical(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        assert self.arg is not None
        x = vm.get(self.arg)

        draw_line(vm, x, vm.graph.ymin, x, vm.graph.ymax)


class DrawF(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        assert self.arg is not None
        graph = vm.graph

        had_x = "X" in vm.vars
        old_x = vm.vars.get("X")

        try:
            for px in range(PIXEL_COLS):
                x, _ = graph.to_coord(px, 0)
                vm.set_var("X", x)

                pixel = graph.to_pixel(x, vm.get(self.arg))
                if pixel is not None:
                    graph.set_pixel(pixel[0], pixel[1], True)
        finally:
            if had_x:
                vm.vars["X"] = old_x
            else:
                vm.vars.pop("X", None)

        vm.io.draw_function()


class Shade(Function):
    def run(self, vm):
        args = self.arg.contents[:]
        assert len(args) in (2, 4, 6)

        graph = vm.graph
        ylower, yupper = args[0], args[1]
        xmin = vm.get(args[2]) if len(args) >= 4 else graph.xmin
        xmax = vm.get(args[3]) if len(args) >= 4 else graph.xmax
        # patres controls how many pixel columns are sampled (a coarser
        # approximation of the real "resolution" parameter's line density);
        # pattern is accepted for signature compatibility but every value
        # renders as solid fill, since the real per-pattern pixel layout
        # wasn't verified against a reference.
        patres = max(1, round(vm.get(args[5]))) if len(args) == 6 else 1

        had_x = "X" in vm.vars
        old_x = vm.vars.get("X")

        try:
            for px in range(0, PIXEL_COLS, patres):
                x, _ = graph.to_coord(px, 0)
                if not (xmin <= x <= xmax):
                    continue

                vm.set_var("X", x)

                lo = vm.get(ylower)
                hi = vm.get(yupper)
                if lo > hi:
                    continue

                lo = max(lo, graph.ymin)
                hi = min(hi, graph.ymax)
                if lo > hi:
                    continue

                p_lo = graph.to_pixel(x, lo)
                p_hi = graph.to_pixel(x, hi)
                if p_lo is None or p_hi is None:
                    continue

                py_top, py_bottom = sorted((p_lo[1], p_hi[1]))
                for py in range(py_top, py_bottom + 1):
                    graph.set_pixel(px, py, True)
        finally:
            if had_x:
                vm.vars["X"] = old_x
            else:
                vm.vars.pop("X", None)

        vm.io.draw_shade()


class Text(Function):
    def call(self, vm, args):
        assert len(args) >= 3
        row, col = args[0], args[1]

        if (
            not isinstance(row, int)
            or not isinstance(col, int)
            or not (0 <= row <= TEXT_MAX_ROW)
            or not (0 <= col <= MAX_COL)
        ):
            raise ExecutionError("ERR:DOMAIN")

        msg = "".join(
            part if isinstance(part, str) else str(vm.disp_round(part))
            for part in args[2:]
        )

        vm.io.draw_text_graph(row, col, msg)


class Radian(Token):
    def run(self, vm):
        vm.degree_mode = False


class Degree(Token):
    def run(self, vm):
        vm.degree_mode = True


class Float(Token):
    def run(self, vm):
        vm.fixed = -1


class Fix(Token):
    absorbs = (Value, Expression)

    def run(self, vm):
        assert self.arg is not None
        arg = vm.get(self.arg)
        assert arg >= 0

        vm.fixed = arg


class AxesOn(Token):
    def run(self, vm):
        vm.graph.axes_on = True


class AxesOff(Token):
    def run(self, vm):
        vm.graph.axes_on = False


class ZStandard(Token):
    def run(self, vm):
        graph = vm.graph
        graph.xmin, graph.xmax, graph.xscl = -10, 10, 1
        graph.ymin, graph.ymax, graph.yscl = -10, 10, 1


class ZDecimal(Token):
    def run(self, vm):
        graph = vm.graph
        graph.xmin, graph.xmax, graph.xscl = -4.7, 4.7, 1
        graph.ymin, graph.ymax, graph.yscl = -3.1, 3.1, 1


class Disp(Token):
    absorbs = (Expression, Variable, Tuple)

    @staticmethod
    def format_matrix(data):
        if isinstance(data, int):
            return data
        out = "[" + str(data[0])
        for row in data[1:]:
            out += "\n " + str(row)
        out += "]"
        return out

    def run(self, vm):
        cur = self.arg
        if not cur:
            self.disp(vm)
            return

        data = None
        if isinstance(cur, ListExpr):
            data = str(vm.get(cur))
        elif isinstance(cur, (MatrixExpr, Matrix)):
            data = self.format_matrix(vm.get(cur))
        elif isinstance(cur, Tuple):
            items = []
            for arg in cur.contents:
                data = vm.get(arg)
                if isinstance(arg, ListExpr):
                    items.append(str(data))
                elif isinstance(arg, (MatrixExpr, Matrix)):
                    items.append(self.format_matrix(data))
                else:
                    items.append(data)
            self.disp(vm, *items)
            return
        else:
            data = vm.get(cur)
        self.disp(vm, data)

    def disp(self, vm, *msgs):
        if not msgs:
            vm.io.disp()
            return
        for msg in msgs:
            vm.io.disp(vm.disp_round(msg))


class Print(Disp):
    absorbs = (Expression, Variable, Tuple)

    def disp(self, vm, *msgs):
        if isinstance(msgs, (tuple, list)):
            vm.io.disp(", ".join(str(vm.disp_round(x)) for x in msgs))
        else:
            vm.io.disp(vm.disp_round(msgs))


class Output(Function):
    def run(self, vm):
        assert len(self.arg) == 3
        row, col, msg = vm.get(self.arg)
        vm.io.output(row, col, vm.disp_round(msg))


class Prompt(Token):
    absorbs = (Expression, Variable, Tuple)

    def run(self, vm):
        if not self.arg:
            raise ExecutionError("%s used without arguments")

        if isinstance(self.arg, Tuple):
            for var in self.arg.contents:
                self.prompt(vm, var)
        else:
            self.prompt(vm, self.arg)

    def prompt(self, vm, var):
        if isinstance(var, Expression):
            var = var.flatten()
        val = vm.io.input(var.token + "?")
        var.set(vm, val)

    def __repr__(self):
        return "Prompt(%s)" % repr(self.arg)


class Input(Token):
    absorbs = (Expression, Variable, Tuple)

    def run(self, vm):
        arg = self.arg
        if not arg:
            raise ExecutionError("Input used without arguments")

        if isinstance(arg, Tuple) and len(arg) == 1 or isinstance(arg, Variable):
            self.prompt(vm, arg)
        elif isinstance(arg, Tuple) and len(arg) == 2:
            self.prompt(vm, arg.contents[1], vm.get(arg.contents[0]))
        else:
            raise ExecutionError("Input used with wrong number of arguments")

    def prompt(self, vm, var, msg="?"):
        if isinstance(var, Expression):
            var = var.flatten()

        if isinstance(var, StrVar):
            is_str = True
        else:
            is_str = False

        val = vm.io.input(msg, is_str)
        var.set(vm, val)


class getKey(Variable):
    def get(self, vm):
        return vm.io.getkey()


class prgm(Token):
    done = False

    def dynamic(self, char):
        if not self.done and char in string.ascii_uppercase:
            self.name += char
            return True
        self.done = True
        return False

    def __init__(self):
        self.name = ""

    def run(self, vm):
        vm.run_prgm(self.name)

    def __repr__(self):
        return "prgm" + self.name


class REPL(Token):
    def run(self, vm):
        from .parse import Parser, ParseError

        if vm.repl_serial != vm.serial:
            vm.repl_serial = vm.serial
            ans = vm.vars.get("Ans")
            if ans is not None:
                d = Disp()
                d.arg = Ans()
                d.run(vm)

        code = None
        while not code:
            repl_line = None
            while not repl_line:
                try:
                    repl_line = input(">>> ")
                except KeyboardInterrupt:
                    print()
                except EOFError:
                    code = [[EOF()]]
                    break

            if not code:
                try:
                    code = Parser(repl_line + "\n").parse()
                except ParseError as e:
                    print(e)

        for line in reversed(code):
            vm.code.insert(self.line, line)

        vm.line, vm.col = self.line, self.col


# date/time commands


def _now(vm):
    return datetime.datetime.now() + vm.clock_offset


class dayOfWk(Function):
    def call(self, vm, args):
        assert len(args) == 3
        date = datetime.datetime(year=args[0], month=args[1], day=args[2])
        return date.isoweekday() % 7 + 1


class getDate(Variable):
    def get(self, vm):
        now = _now(vm)
        return [now.year, now.month, now.day]


class getTime(Variable):
    def get(self, vm):
        now = _now(vm)
        return [now.hour, now.minute, now.second]


class setDate(Function):
    def call(self, vm, args):
        assert len(args) == 3
        y, m, d = (int(a) for a in args)
        now = _now(vm)
        target = datetime.datetime(
            y, m, d, now.hour, now.minute, now.second, now.microsecond
        )
        vm.clock_offset = target - datetime.datetime.now()
        return [y, m, d]


class setTime(Function):
    def call(self, vm, args):
        assert len(args) == 3
        h, mi, s = (int(a) for a in args)
        now = _now(vm)
        target = datetime.datetime(now.year, now.month, now.day, h, mi, s)
        vm.clock_offset = target - datetime.datetime.now()
        return [h, mi, s]


class getDtFmt(Variable):
    def get(self, vm):
        return vm.date_fmt


class setDtFmt(Function):
    def call(self, vm, args):
        assert len(args) == 1
        fmt = int(args[0])
        if fmt not in (1, 2, 3):
            raise ExecutionError("ERR:ARGUMENT")
        vm.date_fmt = fmt
        return fmt


class getTmFmt(Variable):
    def get(self, vm):
        return vm.time_fmt


class setTmFmt(Function):
    def call(self, vm, args):
        assert len(args) == 1
        fmt = int(args[0])
        if fmt not in (12, 24):
            raise ExecutionError("ERR:ARGUMENT")
        vm.time_fmt = fmt
        return fmt


class getDtStr(Function):
    def call(self, vm, args):
        assert len(args) == 1
        fmt = int(args[0])
        now = _now(vm)
        year = now.year % 100
        if fmt == 1:
            return "%02d/%02d/%02d" % (now.month, now.day, year)
        elif fmt == 2:
            return "%02d/%02d/%02d" % (now.day, now.month, year)
        elif fmt == 3:
            return "%02d/%02d/%02d" % (year, now.month, now.day)
        raise ExecutionError("ERR:ARGUMENT")


class getTmStr(Function):
    def call(self, vm, args):
        assert len(args) == 1
        fmt = int(args[0])
        now = _now(vm)
        if fmt == 12:
            hour = now.hour % 12 or 12
            ampm = "AM" if now.hour < 12 else "PM"
            return "%d:%02d %s" % (hour, now.minute, ampm)
        elif fmt == 24:
            return "%02d:%02d" % (now.hour, now.minute)
        raise ExecutionError("ERR:ARGUMENT")


class startTmr(Variable):
    def get(self, vm):
        return int(time.time())


class checkTmr(Function):
    def call(self, vm, args):
        assert len(args) == 1
        return int(time.time()) - int(args[0])


class timeCnv(Function):
    def call(self, vm, args):
        assert len(args) == 1
        seconds = int(args[0])
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return [days, hours, minutes, seconds]


# file IO (not in original TI-Basic)


class ReadFile(Function):
    def call(self, vm, args):
        assert len(args) == 1
        with open(args[0], "r") as f:
            return f.read()
