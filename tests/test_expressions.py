import math

import pytest

from conftest import run


def disp_of(source, inputs=None):
    return run(source, inputs=inputs).io.disps


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Disp 1+2", [3]),
        ("Disp 5-2", [3]),
        ("Disp 2*3", [6]),
        ("Disp 2*4", [8]),
        ("Disp 8/2", [4]),
        ("Disp 6/3", [2]),
        ("Disp 2^3", [8]),
        ("Disp 3^2", [9]),
        ("Disp (2+3)*4", [20]),
        ("Disp 2+3*4", [14]),
        ("Disp -3+5", [2]),
        ("Disp 2!", [2]),
        ("Disp 3!", [6]),
    ],
)
def test_arithmetic(expr, expected):
    assert disp_of(expr) == expected


def test_string_concatenation():
    assert disp_of('Disp "foo" + "bar"') == ["foobar"]


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Disp toString(5)", ["5"]),
        ("Disp toString(-2)", ["-2"]),
        ("Disp toString(3.14)", ["3.14"]),
        ("Disp toString(5.0)", ["5"]),
    ],
)
def test_tostring(expr, expected):
    assert disp_of(expr) == expected


def test_tostring_concatenated_into_a_display_string():
    assert disp_of('Disp "X="+toString(5)') == ["X=5"]


def test_tostring_respects_fix_mode():
    assert disp_of("Fix 2\nDisp toString(3.14159)") == ["3.14"]


def test_tostring_rejects_string_argument():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of('Disp toString("hi")')


def test_trig_functions_default_to_radian_mode():
    assert disp_of("Disp sin(0)") == [0]
    assert disp_of("Radian\nDisp sin(0)") == [0]


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Degree\nDisp sin(90)", 1),
        ("Degree\nDisp cos(180)", -1),
        ("Degree\nDisp tan(45)", 1),
    ],
)
def test_trig_functions_respect_degree_mode(expr, expected):
    assert disp_of(expr)[0] == pytest.approx(expected)


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Degree\nDisp sin-1(1)", 90),
        ("Degree\nDisp cos-1(-1)", 180),
        ("Degree\nDisp tan-1(1)", 45),
    ],
)
def test_inverse_trig_functions_respect_degree_mode(expr, expected):
    assert disp_of(expr)[0] == pytest.approx(expected)


def test_hyperbolic_trig_is_unaffected_by_degree_mode():
    # sinh/cosh/tanh have no notion of an angle, so Degree mode must not
    # touch them - unlike sin/cos/tan they always work on plain reals.
    assert disp_of("Degree\nDisp sinh(0)") == [0]
    assert disp_of("Degree\nDisp cosh(0)") == [1]


def test_inverse_hyperbolic_trig_tokens_are_not_shadowed_by_inverse_trig():
    # sinh-1(/cosh-1(/tanh-1( used to share a token string with
    # sin-1(/cos-1(/tan-1(, so the hyperbolic variants silently won and
    # asin/acos/atan were unreachable.
    assert disp_of("Disp sinh-1(0)") == [0]
    assert disp_of("Disp sin-1(0)") == [0]


def test_degree_symbol_forces_degrees_regardless_of_mode():
    expected = math.sin(math.radians(45))
    assert disp_of("Disp sin(45\xb0)")[0] == pytest.approx(expected)
    assert disp_of("Degree\nDisp sin(45\xb0)")[0] == pytest.approx(expected)


def test_radian_symbol_forces_radians_regardless_of_mode():
    assert disp_of("Degree\nDisp sin((3.14159265358979/2)r)")[0] == pytest.approx(1)
    assert disp_of("Disp sin((3.14159265358979/2)r)")[0] == pytest.approx(1)


def test_dms_literal_evaluates_to_decimal_degrees():
    expected = 30 + 15 / 60 + 20 / 3600
    assert disp_of("Degree\nDisp 30\xb015\x2720\x22")[0] == pytest.approx(expected)


def test_dms_literal_converts_to_radians_in_radian_mode():
    # like the standalone ° symbol, a DMS literal is always entered in
    # degrees but converts to radians when the calculator isn't in
    # Degree mode - it's not immune to the current angle mode.
    expected = math.radians(30 + 15 / 60 + 20 / 3600)
    assert disp_of("Disp 30\xb015\x2720\x22")[0] == pytest.approx(expected)


def test_dms_literal_without_seconds():
    expected = 30 + 15 / 60
    assert disp_of("Degree\nDisp 30\xb015\x27")[0] == pytest.approx(expected)


def test_dms_literal_with_negative_degrees():
    expected = -(30 + 15 / 60 + 20 / 3600)
    assert disp_of("Degree\nDisp -30\xb015\x2720\x22")[0] == pytest.approx(expected)


def test_dms_literal_as_a_function_argument():
    # exercises the bracket-stack lookback path (rather than the flat
    # top-level-line path) for disambiguating " from a string quote.
    expected = math.sin(math.radians(90))
    assert disp_of("Degree\nDisp sin(90\xb00\x270\x22)")[0] == pytest.approx(expected)


def test_string_literals_still_parse_around_dms_literals():
    assert disp_of('Disp 30\xb015\x2720\x22\nDisp "after"') == [
        pytest.approx(math.radians(30 + 15 / 60 + 20 / 3600)),
        "after",
    ]


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Disp 1<2", [1]),
        ("Disp 2<1", [0]),
        ("Disp 1=1", [1]),
        ("Disp 1=2", [0]),
        ("Disp 3>=3", [1]),
        ("Disp 3<=2", [0]),
    ],
)
def test_comparisons(expr, expected):
    assert disp_of(expr) == expected


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Disp 1 and 1", [1]),
        ("Disp 1 and 0", [0]),
        ("Disp 0 or 1", [1]),
        ("Disp 0 or 0", [0]),
        ("Disp not(0)", [1]),
        ("Disp not(1)", [0]),
    ],
)
def test_boolean_logic(expr, expected):
    assert disp_of(expr) == expected


def test_math_functions():
    assert disp_of("Disp abs(-1)") == [1]
    assert disp_of("Disp min(2,1)") == [1]
    assert disp_of("Disp max(5,3)") == [5]
    assert disp_of("Disp sqrt(9)") == [3]
    assert disp_of("Disp gcd(40,30)") == [10]
    assert disp_of("Disp lcm(5,10)") == [10]


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Disp ln(e)", 1),
        ("Disp log(100)", 2),
        ("Disp logBASE(8,2)", 3),
        ("Disp e^(2)", math.e**2),
        ("Disp 10^(3)", 1000),
    ],
)
def test_logarithmic_and_exponential_functions(expr, expected):
    assert disp_of(expr)[0] == pytest.approx(expected)


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Disp ln({1,e,e^2})", [0, 1, 2]),
        ("Disp log({1,10,100})", [0, 1, 2]),
        ("Disp logBASE({8,27},{2,3})", [3, 3]),
        ("Disp logBASE({8,27},2)", [3, pytest.approx(math.log(27, 2))]),
        ("Disp e^({0,1})", [1, math.e]),
        ("Disp 10^({0,2})", [1, 100]),
    ],
)
def test_logarithmic_and_exponential_list_broadcasting(expr, expected):
    assert disp_of(expr) == [expected]


def test_logbase_list_dim_mismatch_raises():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError, match="ERR:DIM MISMATCH"):
        disp_of("Disp logBASE({8,27,64},{2,3})")


def test_logarithmic_domain_errors():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError, match="ERR:DOMAIN"):
        disp_of("Disp ln(0)")
    with pytest.raises(ExecutionError, match="ERR:DOMAIN"):
        disp_of("Disp logBASE(8,1)")


def test_logarithmic_wrong_arg_count_raises_argument_error():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError, match="ERR:ARGUMENT"):
        disp_of("Disp ln(1,2)")
    with pytest.raises(ExecutionError, match="ERR:ARGUMENT"):
        disp_of("Disp e^(1,2)")


def test_logarithmic_rejects_string_arguments():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        disp_of('Disp log("100")')


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Disp 2⁻¹", 0.5),
        ("Disp 5⁻¹", 0.2),
        ("Disp 10⁻¹", 0.1),
        ("Disp 4⁻¹", 0.25),
    ],
)
def test_inverse_operator(expr, expected):
    assert disp_of(expr)[0] == pytest.approx(expected)


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("Disp 2×√4", 2),
        ("Disp 3×√8", 2),
        ("Disp 4×√16", 2),
        ("Disp 2×√9", 3),
        ("Disp 3×√1000", 10),
        ("Disp 3×√1000000", 100),
        ("Disp 3×√-8", -2),
        ("Disp 3×√-27", -3),
    ],
)
def test_nth_root_operator(expr, expected):
    assert disp_of(expr)[0] == pytest.approx(expected)


def test_nth_root_even_root_of_negative_raises():
    from pitybas.common import ExecutionError

    with pytest.raises(ExecutionError, match="ERR:NONREAL ANS"):
        disp_of("Disp 4×√-16")


def test_ans_holds_last_expression_result():
    vm = run("3+4\nDisp Ans")
    assert vm.io.disps == [7]
