"""Characterization tests for known correctness bugs in the expression
evaluator, found while adding test coverage. These are intentionally
marked xfail(strict=True) rather than fixed: if one starts passing, the
underlying bug has been fixed and the xfail marker should be removed.

Bug 1: Base.order() (pitybas/expression.py) groups operators by priority
in a plain dict and iterates it in dict *insertion* order (i.e. the order
operators first appear in the source), instead of sorted by numeric
priority. Per common.Pri, lower numbers should be evaluated first
(EXPONENT=1, MULTDIV=2, ADDSUB=3, ...), but this only happens to work
when the lowest-priority operator in an expression also happens to occur
first in the source text.

Bug 2: FloatOperator.run (pitybas/tokens.py) sets
`decimal.getcontext().prec = max(len(str(left)), len(str(right)))`. For
single-digit operands this sets the precision to 1 significant digit,
so e.g. 3*4 is rounded to 10 instead of 12.

Bug 3: because bug 2 mutates the *global* decimal context and never
restores it, a Mult/Div expression permanently clamps decimal precision
to whatever the last operands required. A later Interpreter.disp_round()
call to round() a Decimal to more digits than that raises
decimal.InvalidOperation instead of displaying a rounded value.

Bug 4: Str0..Str9 (pitybas/tokens.py) are instances of StrVar, not of
the separate (dead) `Str` class. Input.prompt() decides whether to treat
typed input as a raw string via `isinstance(var, Str)`, which is always
False for Str0..Str9, so `Input "msg", Str0` always parses the typed
input as an expression instead of accepting a raw string.
"""
import pytest

from conftest import run


def disp_of(source):
    return run(source).io.disps


@pytest.mark.xfail(strict=True, reason='order() bug: dict insertion order used instead of numeric priority')
@pytest.mark.parametrize('expr,correct', [
    ('Disp 2+3*4', 14),   # currently: (2+3)*4 = 20
    ('Disp 2*3^2', 18),   # currently: (2*3)^2 = 36
    ('Disp 3^2*2', 18),   # currently: 20, because the multiplication also loses precision
])
def test_operator_precedence_follows_source_order_not_priority(expr, correct):
    assert disp_of(expr) == [correct]


@pytest.mark.xfail(strict=True, reason='FloatOperator.run bug: decimal precision tied to operand string length')
@pytest.mark.parametrize('expr,correct', [
    ('Disp 3*4', 12),   # currently rounds to 10 (1 significant digit)
    ('Disp 7*8', 56),   # currently rounds to 60
    ('Disp 9*9', 81),   # currently rounds to 80
])
def test_small_operand_multiplication_loses_precision(expr, correct):
    assert disp_of(expr) == [correct]


@pytest.mark.xfail(strict=True, reason='FloatOperator.run leaks decimal context precision to later round() calls')
def test_fix_after_division_does_not_crash():
    assert disp_of('Fix 2\nDisp 1/3') == [0.33]


@pytest.mark.xfail(strict=True, reason='Str0..Str9 are StrVar, not Str, so Input never treats them as raw strings')
def test_input_treats_str_variable_as_raw_string():
    assert run('Input "name?", Str0\nDisp Str0', inputs=['bob']).io.disps == ['bob']
