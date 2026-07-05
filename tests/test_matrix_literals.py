from conftest import run


def disp_of(source, inputs=None):
    return run(source, inputs=inputs).io.disps


# Real hardware writes adjacent matrix literal rows with no separator
# between them, e.g. "[[1,2][3,4]]". Without a row-boundary fix in
# MatrixExpr.append() (expression.py), the second row merges into the same
# expression as the first, triggering implied multiplication between the
# two rows -- which crashes with "TypeError: can't multiply sequence by
# non-int of type 'list'" since both are plain Python lists.

def test_two_row_matrix_literal_parses_as_separate_rows():
    assert disp_of('[[1,2][3,4]]->[A]\nDisp [A]') == ['[[1, 2]\n [3, 4]]']


def test_three_row_matrix_literal_parses_as_separate_rows():
    assert disp_of('[[1,2,3][4,5,6][7,8,9]]->[A]\nDisp [A]') == [
        '[[1, 2, 3]\n [4, 5, 6]\n [7, 8, 9]]'
    ]


def test_multi_row_matrix_literal_dim():
    assert disp_of('[[1,2][3,4]]->[A]\nDisp dim([A])') == [[2, 2]]


def test_multi_row_matrix_literal_store_and_index():
    assert disp_of('[[1,2][3,4]]->[A]\n5->[A](2,1)\nDisp [A]') == [
        '[[1, 2]\n [5, 4]]'
    ]


def test_single_row_matrix_literal_still_parses_as_one_row():
    """Guards against the fix over-firing: a single-row literal has no
    adjacent MatrixExpr sibling at all, so it must be unaffected."""
    assert disp_of('[[1,2,3,4]]->[A]\nDisp [A]') == ['[[1, 2, 3, 4]]']
