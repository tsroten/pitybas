import pytest

from conftest import run


def disp_of(source, inputs=None):
    return run(source, inputs=inputs).io.disps


@pytest.mark.parametrize('expr,expected', [
    ('Disp 1+2', [3]),
    ('Disp 5-2', [3]),
    ('Disp 2*3', [6]),
    ('Disp 2*4', [8]),
    ('Disp 8/2', [4]),
    ('Disp 6/3', [2]),
    ('Disp 2^3', [8]),
    ('Disp 3^2', [9]),
    ('Disp (2+3)*4', [20]),
    ('Disp 2+3*4', [14]),
    ('Disp -3+5', [2]),
    ('Disp 2!', [2]),
    ('Disp 3!', [6]),
])
def test_arithmetic(expr, expected):
    assert disp_of(expr) == expected


def test_string_concatenation():
    assert disp_of('Disp "foo" + "bar"') == ['foobar']


@pytest.mark.parametrize('expr,expected', [
    ('Disp toString(5)', ['5']),
    ('Disp toString(-2)', ['-2']),
    ('Disp toString(3.14)', ['3.14']),
    ('Disp toString(5.0)', ['5']),
])
def test_tostring(expr, expected):
    assert disp_of(expr) == expected


def test_tostring_concatenated_into_a_display_string():
    assert disp_of('Disp "X="+toString(5)') == ['X=5']


def test_tostring_respects_fix_mode():
    assert disp_of('Fix 2\nDisp toString(3.14159)') == ['3.14']


@pytest.mark.parametrize('expr,expected', [
    ('Disp 1<2', [1]),
    ('Disp 2<1', [0]),
    ('Disp 1=1', [1]),
    ('Disp 1=2', [0]),
    ('Disp 3>=3', [1]),
    ('Disp 3<=2', [0]),
])
def test_comparisons(expr, expected):
    assert disp_of(expr) == expected


@pytest.mark.parametrize('expr,expected', [
    ('Disp 1 and 1', [1]),
    ('Disp 1 and 0', [0]),
    ('Disp 0 or 1', [1]),
    ('Disp 0 or 0', [0]),
    ('Disp not(0)', [1]),
    ('Disp not(1)', [0]),
])
def test_boolean_logic(expr, expected):
    assert disp_of(expr) == expected


def test_math_functions():
    assert disp_of('Disp abs(-1)') == [1]
    assert disp_of('Disp min(2,1)') == [1]
    assert disp_of('Disp max(5,3)') == [5]
    assert disp_of('Disp sqrt(9)') == [3]
    assert disp_of('Disp gcd(40,30)') == [10]
    assert disp_of('Disp lcm(5,10)') == [10]


def test_ans_holds_last_expression_result():
    vm = run('3+4\nDisp Ans')
    assert vm.io.disps == [7]
