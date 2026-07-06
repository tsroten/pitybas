import pytest

from conftest import run


def disp_of(source, inputs=None):
    return run(source, inputs=inputs).io.disps


@pytest.mark.parametrize('expr,expected', [
    ('Disp {1,2,3}+{4,5,6}', [[5, 7, 9]]),
    ('Disp {1,2,3}-{4,5,6}', [[-3, -3, -3]]),
    ('Disp {1,2,3}*{4,5,6}', [[4, 10, 18]]),
    ('Disp {10,20,30}/{2,4,5}', [[5, 5, 6]]),
])
def test_list_list_is_elementwise(expr, expected):
    assert disp_of(expr) == expected


@pytest.mark.parametrize('expr,expected', [
    ('Disp {1,2,3}+5', [[6, 7, 8]]),
    ('Disp 5+{1,2,3}', [[6, 7, 8]]),
    ('Disp {1,2,3}-1', [[0, 1, 2]]),
    ('Disp 10-{1,2,3}', [[9, 8, 7]]),
    ('Disp {1,2,3}*2', [[2, 4, 6]]),
    ('Disp 2*{1,2,3}', [[2, 4, 6]]),
    ('Disp {10,20,30}/2', [[5, 10, 15]]),
])
def test_scalar_broadcasts_against_list(expr, expected):
    assert disp_of(expr) == expected


def test_list_list_dim_mismatch_raises():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError):
        disp_of('Disp {1,2,3}+{1,2}')


@pytest.mark.parametrize('expr,expected', [
    ('[[1,2][3,4]]->[A]\n[[5,6][7,8]]->[B]\nDisp [A]+[B]', [[[6, 8], [10, 12]]]),
    ('[[1,2][3,4]]->[A]\n[[5,6][7,8]]->[B]\nDisp [A]-[B]', [[[-4, -4], [-4, -4]]]),
])
def test_matrix_matrix_addsub_is_elementwise(expr, expected):
    assert disp_of(expr) == expected


def test_matrix_matrix_mult_is_real_matrix_multiplication():
    assert disp_of(
        '[[1,2][3,4]]->[A]\n[[1,0][0,1]]->[B]\nDisp [A]*[B]'
    ) == [[[1, 2], [3, 4]]]

    assert disp_of(
        '[[1,2][3,4]]->[A]\n[[5,6][7,8]]->[B]\nDisp [A]*[B]'
    ) == [[[19, 22], [43, 50]]]


@pytest.mark.parametrize('expr,expected', [
    ('[[1,2][3,4]]->[A]\nDisp [A]+2', [[[3, 4], [5, 6]]]),
    ('[[1,2][3,4]]->[A]\nDisp 2+[A]', [[[3, 4], [5, 6]]]),
    ('[[1,2][3,4]]->[A]\nDisp [A]*2', [[[2, 4], [6, 8]]]),
    ('[[2,4][6,8]]->[A]\nDisp [A]/2', [[[1, 2], [3, 4]]]),
])
def test_scalar_broadcasts_against_matrix(expr, expected):
    assert disp_of(expr) == expected


def test_matrix_matrix_dim_mismatch_raises():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError):
        disp_of('[[1,2][3,4]]->[A]\n[[1,2,3]]->[B]\nDisp [A]*[B]')


def test_list_and_matrix_together_raises():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError):
        disp_of('[[1,2][3,4]]->[A]\nDisp {1,2}+[A]')
