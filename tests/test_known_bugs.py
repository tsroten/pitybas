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

Bug 5 (fixed): nCr.op (pitybas/tokens.py) called `math.fact`, which does
not exist on the `math` module (it's `math.factorial`), so any use of
nCr raised AttributeError. Fixed to call `math.factorial` and, to match
the sibling `nPr` operator, use `//` so the result is an int rather than
a float.

Bug 6 (fixed): lcm.call (pitybas/tokens.py) reduced a list second
argument with `a = self.lcm_list(*b)` instead of `b = self.lcm_list(*b)`,
clobbering the first argument and leaving the second argument as an
unreduced list. `lcm(a, b)` then did `a % list`, raising TypeError.
Fixed to assign the reduced value back to `b`.

Bug 7 (fixed): Menu.run (pitybas/tokens.py) built each menu's
(description, label) pairs with a bare `zip()`, a single-use iterator.
IO.menu() (pitybas/io/simple.py, pitybas/io/vt100.py) loops until a
valid choice is entered, re-iterating those pairs on every retry -- so
after the first (invalid) attempt exhausted the zip, every retry
rendered zero options and no choice could ever succeed. Fixed by
materializing the zip into a list.

Bug 8 (fixed): cli.main (pitybas/cli.py) printed
`'-===[ Running %s ]===-' % args[0]` unconditionally inside the
`--verbose` branch. Since `args` is empty when no filename is given
(REPL mode), `pb -v` raised IndexError before the REPL could start.
Fixed to only print that line when a filename was given.

Bug 9 (fixed): Lbl.guess_label (pitybas/tokens.py) rendered a letter+digit
label (e.g. "M1", which parses as implied multiplication -- Variable *
Value, not a single token) by falling back to `str(arg.flatten())`. That
joins each raw token's `.token` attribute, but `Value.token` is a fixed
class-level placeholder string ("Value"), not the digit actually parsed.
So every "<letter><digit>" label collapsed to the same string regardless
of the digit, and `Goto M2`/`Goto M3` both resolved to whichever `Lbl
M<n>` appeared first in the source. Fixed by reconstructing the label
from each part's real value (`Variable.token` / `Value.value`) instead of
relying on the generic `.token` placeholder.

Bug 10 (fixed): VT.getch (pitybas/io/vt100.py) translated escape
sequences (arrow keys) into the name strings ('up', 'down', ...) that
the `keycodes` dict is keyed by, but returned the raw '\r' byte for
Enter instead of translating it to 'enter'. IO.getkey() looks up
`keycodes[key]`, so pressing Enter always missed the dict and getkey()
returned 0 no matter how many times it was pressed. Fixed by having
getch() translate '\r'/'\n' to the string 'enter' before returning, the
same way arrow keys are translated.
"""
import io as std_io
import types

import pytest

from conftest import MockIO, run


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


def test_nCr_does_not_crash():
    assert disp_of('Disp 5 nCr 2') == [10]


def test_lcm_reduces_second_list_argument():
    assert disp_of('Disp lcm(4,{2,3})') == [12]


def test_menu_entries_are_reusable_across_retries():
    """Reproduces bug 7: a MockIO whose menu() re-iterates `entries` twice
    (as the real IO backends do on an invalid-choice retry) must see the
    same options both times."""
    from pitybas.interpret import Interpreter

    class MenuIO(MockIO):
        def menu(self, menu):
            for title, entries in menu:
                first_pass = list(entries)
                second_pass = list(entries)

            assert first_pass, 'menu should have options on the first pass'
            assert first_pass == second_pass, \
                'menu entries were exhausted on the second pass'

            _, label = second_pass[0]
            return label

    vm = Interpreter.from_string(
        'Menu("t","e1",A,"e2",B)\nDisp "no\nLbl A\nDisp "yes',
        io=lambda vm: MenuIO(vm),
    )
    vm.execute()
    assert vm.io.disps == ['yes']


def test_verbose_repl_with_no_filename_does_not_crash(monkeypatch):
    from pitybas.cli import main

    monkeypatch.setattr('sys.stdin', std_io.StringIO(''))
    main(['-v'])


def test_goto_letter_digit_label_reaches_matching_label():
    """Reproduces bug 9: Goto M2 must land at Lbl M2, not Lbl M1, even
    though both labels parse as the same kind of implied-multiplication
    expression (Variable * Value)."""
    vm = run(
        'Goto M2\n'
        'Lbl M1\nDisp "one"\n'
        'Lbl M2\nDisp "two"\n'
        'Lbl M3\nDisp "three"'
    )
    assert vm.io.disps == ['two', 'three']


def test_getkey_returns_enter_keycode_for_carriage_return(monkeypatch):
    """Reproduces bug 10: pressing Enter in raw tty mode sends '\\r', which
    must be translated to the 'enter' string (as arrow keys are translated
    to 'up'/'down'/etc.) so it can be found in the keycodes dict."""
    from pitybas.interpret import Interpreter
    from pitybas.io import vt100

    monkeypatch.setattr(vt100.termios, 'tcgetattr', lambda fd: None)
    monkeypatch.setattr(vt100.termios, 'tcsetattr', lambda fd, when, attrs: None)
    monkeypatch.setattr(vt100.tty, 'setraw', lambda fd: None)
    monkeypatch.setattr(vt100.select, 'select', lambda r, w, x, timeout: (r, [], []))
    monkeypatch.setattr(vt100.sys, 'stdin', types.SimpleNamespace(
        fileno=lambda: 0, read=lambda n: '\r',
    ))

    io = vt100.IO(Interpreter.from_string(''))
    assert io.getkey() == 105
