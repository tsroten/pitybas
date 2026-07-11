import math

import pytest

from conftest import run
from pitybas.common import ExecutionError

# Result-variable spellings use a decomposed combining macron for x̄/ȳ (no
# precomposed codepoint exists for x-macron), matching how the tokens register.
XBAR = "x̄"
YBAR = "ȳ"
SIGMA_X = "Σx"
SIGMA_X2 = "Σx²"
SIGMA_Y = "Σy"
SIGMA_Y2 = "Σy²"
SIGMA_XY = "Σxy"
STDDEVP_X = "σx"
STDDEVP_Y = "σy"


# --- mean( -----------------------------------------------------------------


def test_mean_whole_list():
    vm = run("{1,2,3,4,5}->lA\nDisp mean(lA)")
    assert vm.io.disps == [3]


def test_mean_of_list_literal():
    vm = run("Disp mean({2,4,6})")
    assert vm.io.disps == [4]


def test_mean_with_freqlist():
    # (1*2 + 2*1 + 3*1) / 4 = 1.75
    vm = run("{1,2,3}->lA\n{2,1,1}->lB\nDisp mean(lA,lB)")
    assert vm.io.disps == [1.75]


# --- median( ---------------------------------------------------------------


def test_median_odd_length():
    vm = run("Disp median({3,1,2})")
    assert vm.io.disps == [2]


def test_median_even_length_averages_middle_pair():
    vm = run("Disp median({1,2,3,4})")
    assert vm.io.disps == [2.5]


def test_median_with_freqlist_expands_values():
    # frequencies expand to [1,2,3,3,3]; median is 3
    vm = run("Disp median({1,2,3},{1,1,3})")
    assert vm.io.disps == [3]


def test_median_fractional_frequency_raises():
    with pytest.raises(ExecutionError, match="ERR:DOMAIN"):
        run("Disp median({1,2,3},{1,0.5,1})")


# --- variance( / stdDev( ---------------------------------------------------


def test_variance_is_sample_variance():
    # sample variance of 1..5 divides by n-1 = 4 -> 2.5
    vm = run("Disp variance({1,2,3,4,5})")
    assert vm.io.disps == [2.5]


def test_stddev_is_sample_std_dev():
    vm = run("Disp stdDev({1,2,3,4,5})")
    assert vm.io.disps[0] == pytest.approx(math.sqrt(2.5))


def test_stddev_with_freqlist():
    # {2,4,4,4,5,5,7,9} as (value, freq) pairs -> sample std dev
    vm = run("{2,4,5,7,9}->lA\n{1,3,2,1,1}->lB\nDisp stdDev(lA,lB)")
    assert vm.io.disps[0] == pytest.approx(math.sqrt(32 / 7))


def test_variance_single_element_raises():
    with pytest.raises(ExecutionError, match="ERR:STAT"):
        run("{5}->lA\nDisp variance(lA)")


def test_mismatched_freqlist_length_raises():
    with pytest.raises(ExecutionError, match="ERR:DIM MISMATCH"):
        run("Disp mean({1,2,3},{1,1})")


# --- 1-Var Stats -----------------------------------------------------------


def test_one_var_stats_populates_result_variables():
    prog = (
        "{1,2,3,4,5,6,7,8,9}->lA\n"
        "1-Var Stats lA\n"
        f"Disp {XBAR}\n"
        f"Disp {SIGMA_X}\n"
        f"Disp {SIGMA_X2}\n"
        "Disp n\n"
        "Disp minX\n"
        "Disp Q1\n"
        "Disp Med\n"
        "Disp Q3\n"
        "Disp maxX"
    )
    vm = run(prog)
    assert vm.io.disps == [5, 45, 285, 9, 1, 2.5, 5, 7.5, 9]


def test_one_var_stats_sample_and_population_deviation():
    prog = f"{{1,2,3,4,5}}->lA\n1-Var Stats lA\nDisp Sx\nDisp {STDDEVP_X}"
    vm = run(prog)
    assert vm.io.disps[0] == pytest.approx(math.sqrt(2.5))
    assert vm.io.disps[1] == pytest.approx(math.sqrt(2.0))


def test_one_var_stats_defaults_to_l1():
    vm = run("{10,20,30}->L1\n1-Var Stats\nDisp " + XBAR + "\nDisp n")
    assert vm.io.disps == [20, 3]


def test_one_var_stats_with_freqlist():
    # values 1,2,3 with frequencies 2,1,1 -> mean 1.75, n 4
    vm = run("{1,2,3}->lA\n{2,1,1}->lB\n1-Var Stats lA,lB\nDisp " + XBAR + "\nDisp n")
    assert vm.io.disps == [1.75, 4]


# --- 2-Var Stats -----------------------------------------------------------


def test_two_var_stats_populates_x_and_y_variables():
    prog = (
        "{1,2,3}->lA\n"
        "{2,4,6}->lB\n"
        "2-Var Stats lA,lB\n"
        f"Disp {XBAR}\n"
        f"Disp {YBAR}\n"
        f"Disp {SIGMA_X}\n"
        f"Disp {SIGMA_Y}\n"
        f"Disp {SIGMA_Y2}\n"
        f"Disp {SIGMA_XY}\n"
        "Disp n"
    )
    vm = run(prog)
    assert vm.io.disps == [2, 4, 6, 12, 56, 28, 3]


def test_two_var_stats_defaults_to_l1_and_l2():
    prog = "{1,2,3}->L1\n{4,5,6}->L2\n2-Var Stats\nDisp " + XBAR + "\nDisp " + YBAR
    vm = run(prog)
    assert vm.io.disps == [2, 5]


def test_two_var_stats_mismatched_lengths_raises():
    with pytest.raises(ExecutionError, match="ERR:DIM MISMATCH"):
        run("{1,2,3}->lA\n{4,5}->lB\n2-Var Stats lA,lB")
