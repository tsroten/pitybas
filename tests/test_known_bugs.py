"""Regression tests for correctness bugs that were previously
characterized here as known/expected failures. All four have since been
fixed; kept as plain tests (rather than deleted or folded elsewhere) so a
regression shows up here first.

Bug 1 (fixed): Base.order() (pitybas/expression.py) grouped operators by
priority in a plain dict and iterated it in dict *insertion* order (i.e.
the order operators first appear in the source), instead of sorted by
numeric priority. Per common.Pri, lower numbers should be evaluated first
(EXPONENT=1, MULTDIV=2, ADDSUB=3, ...). Fixed by sorting the priority
keys before flattening them into the evaluation order.

Bug 2 (fixed): FloatOperator.run (pitybas/tokens.py) set
`decimal.getcontext().prec = max(len(str(left)), len(str(right)))`. For
single-digit operands this set the precision to 1 significant digit, so
e.g. 3*4 was rounded to 10 instead of 12. The Decimal coercion was a
leftover Python 2 workaround (to force true division on ints) that Python
3's native `/` already handles, so it was removed outright.

Bug 3 (fixed): because bug 2 mutated the *global* decimal context and
never restored it, a Mult/Div expression permanently clamped decimal
precision to whatever the last operands required. A later
Interpreter.disp_round() call to round() a Decimal to more digits than
that raised decimal.InvalidOperation instead of displaying a rounded
value. Fixed as a side effect of removing the Decimal coercion in bug 2.

Bug 4 (fixed): Str0..Str9 (pitybas/tokens.py) are instances of StrVar,
not of the separate (and now-unused) `Str` class. Input.prompt() decided
whether to treat typed input as a raw string via `isinstance(var, Str)`,
which was always False for Str0..Str9, so `Input "msg", Str0` always
parsed the typed input as an expression instead of accepting a raw
string. Fixed by checking `isinstance(var, StrVar)` instead.
"""
import pytest

from conftest import run


def disp_of(source):
    return run(source).io.disps


@pytest.mark.parametrize('expr,correct', [
    ('Disp 2+3*4', 14),
    ('Disp 2*3^2', 18),
    ('Disp 3^2*2', 18),
])
def test_operator_precedence_follows_numeric_priority(expr, correct):
    assert disp_of(expr) == [correct]


@pytest.mark.parametrize('expr,correct', [
    ('Disp 3*4', 12),
    ('Disp 7*8', 56),
    ('Disp 9*9', 81),
])
def test_small_operand_multiplication_keeps_precision(expr, correct):
    assert disp_of(expr) == [correct]


def test_fix_after_division_does_not_crash():
    assert disp_of('Fix 2\nDisp 1/3') == [0.33]


def test_input_treats_str_variable_as_raw_string():
    assert run('Input "name?", Str0\nDisp Str0', inputs=['bob']).io.disps == ['bob']
