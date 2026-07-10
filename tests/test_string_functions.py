import pytest

from conftest import run
from pitybas.common import ExecutionError


def disp_of(source):
    return run(source).io.disps


@pytest.mark.parametrize(
    "expr,expected",
    [
        # Guidebook worked example (p.271): S is the 4th character -> 1-based 4.
        ('Disp inString("PQRSTUV","STU")', [4]),
        # Guidebook second worked example: search starting from the 4th character.
        ('Disp inString("ABCABC","ABC",4)', [4]),
        # Match at the very start is 1-based position 1, not 0.
        ('Disp inString("HELLO","H")', [1]),
        # Substring not present returns 0 (not Python's -1).
        ('Disp inString("ABC","Z")', [0]),
        # start beyond the string length returns 0.
        ('Disp inString("ABC","A",9)', [0]),
    ],
)
def test_instring(expr, expected):
    assert disp_of(expr) == expected


@pytest.mark.parametrize(
    "expr",
    [
        # start below 1 is invalid on real hardware (ERR:DOMAIN), and must not
        # be passed through to str.find as a negative (search-from-end) offset.
        'Disp inString("ABCABC","ABC",0)',
        'Disp inString("ABCABC","ABC",-1)',
    ],
)
def test_instring_start_below_one_is_domain_error(expr):
    with pytest.raises(ExecutionError, match="ERR:DOMAIN"):
        disp_of(expr)
