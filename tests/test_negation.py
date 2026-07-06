import pytest

from pitybas.common import ExpressionError
from conftest import run


def disp_of(source, inputs=None):
    return run(source, inputs=inputs).io.disps


# --- Existing hyphen ('-') negation behavior -------------------------------
#
# pitybas has no general unary-minus token for '-': a leading hyphen only
# becomes a negative literal when a digit immediately follows (handled at
# the lexer level in Parser.number()), or when it is the *sole* token so
# far in an expression/sub-expression (handled by the "minus sign implies
# * -1" special case in expression.Base.append()). These tests characterize
# that existing behavior, including its known gap, so a future change can't
# silently regress it.

@pytest.mark.parametrize('expr,expected', [
    ('Disp -5', [-5]),
    ('Disp -3+5', [2]),
    ('Disp 3--2', [5]),
    ('Disp 3+-2', [1]),
    ('Disp 3*-2', [-6]),
    ('Disp --5', [5]),
])
def test_hyphen_negative_literal(expr, expected):
    assert disp_of(expr) == expected


def test_hyphen_negates_leading_variable():
    assert disp_of('5->H\nDisp -H') == [-5]


def test_hyphen_negates_leading_parenthesized_expression():
    assert disp_of('5->H\nDisp -(H+1)') == [-6]


def test_hyphen_negates_leading_function_call():
    assert disp_of('Disp -sin(0)') == [0]


def test_hyphen_negates_leading_list_element():
    assert disp_of('{1,2,3}->∟1\nDisp -∟1(1)') == [-1]


def test_hyphen_unary_negation_of_non_digit_operand_requires_leading_position():
    """Known gap: unary '-' only collapses to "-1 * X" when it is the sole
    token so far in its expression. A hyphen negating a variable anywhere
    else (e.g. right after another operator) isn't recognized as unary and
    raises, rather than being silently misevaluated."""
    with pytest.raises(ExpressionError):
        run('5->H\nDisp 3+-H')


# --- Negation glyph ('⁻') behavior ------------------------------------------
#
# '⁻' (the real calculator's dedicated negation key, distinct from the '-'
# subtraction token) always means unary negation, in any position -- unlike
# '-', it's never ambiguous with a binary operator. Base.append() collapses
# it to "-1 * X" unconditionally, so (unlike '-') it also covers the
# "negation not in the leading position" case that '-' can't.

@pytest.mark.parametrize('expr,expected', [
    ('Disp ⁻5', [-5]),
    ('Disp ⁻⁻5', [5]),
    ('Disp 3+⁻2', [1]),
    ('Disp 3*⁻2', [-6]),
])
def test_negation_glyph_literal(expr, expected):
    assert disp_of(expr) == expected


def test_negation_glyph_negates_leading_variable():
    assert disp_of('5->H\nDisp ⁻H') == [-5]


def test_negation_glyph_negates_leading_parenthesized_expression():
    assert disp_of('5->H\nDisp ⁻(H+1)') == [-6]


def test_negation_glyph_negates_leading_function_call():
    assert disp_of('Disp ⁻sin(0)') == [0]


def test_negation_glyph_negates_leading_list_element():
    assert disp_of('{1,2,3}->∟1\nDisp ⁻∟1(1)') == [-1]


def test_negation_glyph_double_negates_variable():
    assert disp_of('5->H\nDisp ⁻⁻H') == [5]


def test_negation_glyph_negates_variable_after_leading_operator():
    """Unlike '-', '⁻' also handles negation that doesn't lead the
    expression -- this is the exact gap documented in
    test_hyphen_unary_negation_of_non_digit_operand_requires_leading_position."""
    assert disp_of('5->H\nDisp 3+⁻H') == [-2]
    assert disp_of('5->H\nDisp 3*⁻H') == [-15]


def test_negation_glyph_in_comparison():
    assert disp_of('5->W\nDisp W=⁻5') == [0]
    assert disp_of('⁻5->W\nDisp W=⁻5') == [1]


# --- Negation tilde ('~') behavior ------------------------------------------
#
# '~' is the plaintext ASCII stand-in for the same dedicated negation key as
# '⁻' -- it's how the token shows up when a .8xp program is dumped to text,
# since ASCII has no raised-minus glyph. It should behave identically to
# '⁻', and must stay distinct from the '~=' (not-equals) token.

@pytest.mark.parametrize('expr,expected', [
    ('Disp ~5', [-5]),
    ('Disp ~~5', [5]),
    ('Disp 3+~2', [1]),
    ('Disp 3*~2', [-6]),
])
def test_negation_tilde_literal(expr, expected):
    assert disp_of(expr) == expected


def test_negation_tilde_negates_leading_variable():
    assert disp_of('5->H\nDisp ~H') == [-5]


def test_negation_tilde_negates_leading_parenthesized_expression():
    assert disp_of('5->H\nDisp ~(H+1)') == [-6]


def test_negation_tilde_negates_leading_function_call():
    assert disp_of('Disp ~sin(0)') == [0]


def test_negation_tilde_negates_leading_list_element():
    assert disp_of('{1,2,3}->∟1\nDisp ~∟1(1)') == [-1]


def test_negation_tilde_double_negates_variable():
    assert disp_of('5->H\nDisp ~~H') == [5]


def test_negation_tilde_negates_variable_after_leading_operator():
    assert disp_of('5->H\nDisp 3+~H') == [-2]
    assert disp_of('5->H\nDisp 3*~H') == [-15]


def test_negation_tilde_in_comparison():
    assert disp_of('5->W\nDisp W=~5') == [0]
    assert disp_of('~5->W\nDisp W=~5') == [1]


def test_negation_tilde_distinct_from_not_equals():
    assert disp_of('5->W\nDisp W~=6') == [1]
    assert disp_of('5->W\nDisp W~=5') == [0]
