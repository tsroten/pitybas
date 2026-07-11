import pytest

from conftest import run
from pitybas.common import ExecutionError


def disp_of(source):
    return run(source).io.disps


# nDeriv( -----------------------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Disp nDeriv(X^2,X,3)", 6),
        ("Disp nDeriv(X^3,X,2)", 12),
        ("Disp nDeriv(3X,X,10)", 3),
        ("Disp nDeriv(sin(X),X,0)", 1),
        # explicit step size H
        ("Disp nDeriv(X^2,X,3,.01)", 6),
    ],
)
def test_nderiv(source, expected):
    (result,) = disp_of(source)
    assert result == pytest.approx(expected, abs=1e-3)


def test_nderiv_zero_step_is_domain_error():
    with pytest.raises(ExecutionError, match="ERR:DOMAIN"):
        disp_of("Disp nDeriv(X^2,X,3,0)")


def test_nderiv_wrong_arg_count():
    with pytest.raises(ExecutionError, match="ERR:ARGUMENT"):
        disp_of("Disp nDeriv(X^2,X)")


def test_nderiv_list_value_is_data_type_error():
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of("Disp nDeriv(X,X,{1,2},.001)")


def test_nderiv_list_step_is_data_type_error():
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of("Disp nDeriv(X,X,3,{.001,.002})")


# fnInt( ------------------------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Disp fnInt(X^2,X,0,3)", 9),
        ("Disp fnInt(X^3,X,0,2)", 4),
        ("Disp fnInt(2X,X,0,5)", 25),
        ("Disp fnInt(sin(X),X,0,π)", 2),
        # reversed bounds flip the sign
        ("Disp fnInt(X^2,X,3,0)", -9),
        # equal bounds integrate to zero
        ("Disp fnInt(X^2,X,4,4)", 0),
    ],
)
def test_fnint(source, expected):
    (result,) = disp_of(source)
    assert result == pytest.approx(expected, abs=1e-4)


def test_fnint_wrong_arg_count():
    with pytest.raises(ExecutionError, match="ERR:ARGUMENT"):
        disp_of("Disp fnInt(X^2,X,0)")


def test_fnint_list_bound_is_data_type_error():
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of("Disp fnInt(X^2,X,{0,1},3)")


# fMax( / fMin( -----------------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Disp fMin((X-2)^2,X,0,5)", 2),
        ("Disp fMin(X^2,X,-3,3)", 0),
        # golden-section shouldn't care about argument order of the bounds
        ("Disp fMin((X-2)^2,X,5,0)", 2),
    ],
)
def test_fmin(source, expected):
    (result,) = disp_of(source)
    assert result == pytest.approx(expected, abs=1e-3)


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Disp fMax(-(X-2)^2,X,0,5)", 2),
        ("Disp fMax(6X-X^2,X,0,6)", 3),
    ],
)
def test_fmax(source, expected):
    (result,) = disp_of(source)
    assert result == pytest.approx(expected, abs=1e-3)


def test_fmax_wrong_arg_count():
    with pytest.raises(ExecutionError, match="ERR:ARGUMENT"):
        disp_of("Disp fMax(X,X,0)")


def test_fmin_list_bound_is_data_type_error():
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of("Disp fMin(X^2,X,{0,1},5)")


# solve( ------------------------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        # the guess selects which root the outward bracket search converges to
        ("Disp solve(X^2-4,X,3)", 2),
        ("Disp solve(X^2-4,X,-3)", -2),
        ("Disp solve(2X-8,X,0)", 4),
        # bounds bracketing a sign change use bisection
        ("Disp solve(X^2-4,X,3,{0,5})", 2),
        ("Disp solve(X^2-4,X,0,{-5,0})", -2),
    ],
)
def test_solve(source, expected):
    (result,) = disp_of(source)
    assert result == pytest.approx(expected, abs=1e-4)


def test_solve_no_root_raises():
    with pytest.raises(ExecutionError, match="ERR:NO SIGN CHNG"):
        disp_of("Disp solve(X^2+1,X,3,{0,5})")


def test_solve_no_bounds_no_sign_change_raises():
    # matches real hardware exactly: TI's own knowledge base uses solve(X^2,X,guess)
    # as *the* canonical ERR:NO SIGN CHNG example, since X^2 never crosses zero -
    # this must raise even with no {lower,upper} given (default bounds are
    # {-1E99,1E99}, not "fall back to an unconstrained root finder")
    with pytest.raises(ExecutionError, match="ERR:NO SIGN CHNG"):
        disp_of("Disp solve(X^2,X,1)")


def test_solve_wrong_arg_count():
    with pytest.raises(ExecutionError, match="ERR:ARGUMENT"):
        disp_of("Disp solve(X^2-4,X)")


def test_solve_list_guess_is_data_type_error():
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of("Disp solve(X^2-4,X,{3,4})")


def test_solve_list_bound_element_is_data_type_error():
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of("{1,2}->L1\nDisp solve(X^2-4,X,3,{L1,5})")


# remainder( --------------------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Disp remainder(17,5)", 2),
        # truncated (toward-zero) division: result carries the dividend's sign
        ("Disp remainder(-17,5)", -2),
        ("Disp remainder(17,-5)", 2),
        ("Disp remainder(-17,-5)", -2),
        ("Disp remainder(20,4)", 0),
    ],
)
def test_remainder_scalar(source, expected):
    assert disp_of(source) == [expected]


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Disp remainder({17,18,19},5)", [2, 3, 4]),
        ("Disp remainder(17,{5,7})", [2, 3]),
        ("Disp remainder({17,18},{5,7})", [2, 4]),
    ],
)
def test_remainder_list_broadcasting(source, expected):
    assert disp_of(source) == [expected]


def test_remainder_divide_by_zero():
    with pytest.raises(ExecutionError, match="ERR:DIVIDE BY 0"):
        disp_of("Disp remainder(5,0)")


def test_remainder_dim_mismatch():
    with pytest.raises(ExecutionError, match="ERR:DIM MISMATCH"):
        disp_of("Disp remainder({1,2,3},{1,2})")


def test_remainder_wrong_arg_count():
    with pytest.raises(ExecutionError, match="ERR:ARGUMENT"):
        disp_of("Disp remainder(5)")


def test_remainder_matrix_rejected():
    # remainder( isn't defined for Matrix operands on real hardware (unlike
    # Lists), matching how nPr/nCr (also scalar-domain functions) reject them
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of("[[1,2][3,4]]->[A]\n[[1,1][1,1]]->[B]\nDisp remainder([A],[B])")
