import pytest

from conftest import run
from pitybas.common import ExecutionError


def disp_of(source):
    return run(source).io.disps


@pytest.mark.parametrize(
    "operator,expected",
    [
        ("nPr", [[20, 30, 42]]),
        ("nCr", [[10, 15, 21]]),
    ],
)
def test_probability_operator_supports_list_scalar(operator, expected):
    assert disp_of(f"Disp {{5,6,7}} {operator} 2") == expected


@pytest.mark.parametrize(
    "operator,expected",
    [
        ("nPr", [[5, 20, 60]]),
        ("nCr", [[5, 10, 10]]),
    ],
)
def test_probability_operator_supports_scalar_list(operator, expected):
    assert disp_of(f"Disp 5 {operator} {{1,2,3}}") == expected


@pytest.mark.parametrize(
    "operator,expected",
    [
        ("nPr", [[5, 30, 210]]),
        ("nCr", [[5, 15, 35]]),
    ],
)
def test_probability_operator_supports_pairwise_lists(operator, expected):
    assert disp_of(f"Disp {{5,6,7}} {operator} {{1,2,3}}") == expected


@pytest.mark.parametrize("operator", ["nPr", "nCr"])
def test_probability_operator_rejects_unequal_list_lengths(operator):
    with pytest.raises(ExecutionError, match="ERR:DIM MISMATCH"):
        disp_of(f"Disp {{5,6}} {operator} {{1,2,3}}")


@pytest.mark.parametrize("operator", ["nPr", "nCr"])
@pytest.mark.parametrize(
    "expression",
    [
        "[A] {operator} 2",
        "5 {operator} [A]",
        "[A] {operator} [B]",
    ],
)
def test_probability_operator_rejects_matrices(operator, expression):
    source = (
        "[[1,2][3,4]]->[A]\n"
        "[[1,0][0,1]]->[B]\n"
        f"Disp {expression.format(operator=operator)}"
    )

    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of(source)


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("5 nPr 2", [20]),
        ("5 nCr 2", [10]),
    ],
)
def test_probability_operator_preserves_scalar_integer_results(expression, expected):
    assert disp_of(f"Disp {expression}") == expected
