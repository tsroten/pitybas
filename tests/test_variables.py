import pytest

from conftest import run
from pitybas.common import ExecutionError


def test_simple_variable_store_and_get():
    vm = run('5->A\nDisp A')
    assert vm.io.disps == [5]
    assert vm.vars['A'] == 5


def test_variable_defaults_to_zero():
    vm = run('Disp A')
    assert vm.io.disps == [0]


def test_strict_mode_raises_on_undefined_variable():
    with pytest.raises(ExecutionError, match='ERR:UNDEFINED'):
        run('Disp A', strict=True)


def test_strict_mode_allows_defined_variable():
    vm = run('5->A\nDisp A', strict=True)
    assert vm.io.disps == [5]


def test_chained_store():
    vm = run('1->D->E\nDisp D\nDisp E')
    assert vm.io.disps == [1, 1]


def test_store_closes_open_brackets():
    vm = run('3+(1+2->C\nDisp C')
    assert vm.io.disps == [6]


def test_string_variable_defaults_to_empty():
    vm = run('Disp Str0')
    assert vm.io.disps == ['']


def test_string_variable_store_and_get():
    vm = run('"hi"->Str0\nDisp Str0')
    assert vm.io.disps == ['hi']


def test_ans_updates_after_bare_expression():
    vm = run('10\nDisp Ans')
    assert vm.io.disps == [10]


def test_list_store_and_index():
    vm = run('{1,2,3}->lTEST\nDisp lTEST\n5->lTEST(1)\nDisp lTEST')
    assert vm.io.disps == [[1, 2, 3], [5, 2, 3]]


def test_list_accepts_uppercase_l():
    vm = run('{1,2,3}->L1\nDisp L1\n5->L1(1)\nDisp L1')
    assert vm.io.disps == [[1, 2, 3], [5, 2, 3]]


def test_uppercase_l_list_and_lowercase_l_list_are_the_same_list():
    vm = run('{1,2,3}->L1\nDisp l1')
    assert vm.io.disps == [[1, 2, 3]]


def test_small_capital_l_list_store_and_index():
    vm = run(u'{1,2,3}->ʟNUMS\nDisp ʟNUMS\n5->ʟNUMS(1)\nDisp ʟNUMS')
    assert vm.io.disps == [[1, 2, 3], [5, 2, 3]]


def test_small_capital_l_list_same_as_right_angle_list():
    vm = run(u'{1,2,3}->ʟNUMS\nDisp ∟NUMS')
    assert vm.io.disps == [[1, 2, 3]]


def test_list_subscript_digit_store_and_get():
    vm = run('{1,2,3}->L₁\nDisp L₁\n5->L₁(1)\nDisp L₁')
    assert vm.io.disps == [[1, 2, 3], [5, 2, 3]]


def test_list_subscript_digit_same_as_plain_digit():
    vm = run('{1,2,3}->L₁\nDisp L1\nDisp l1')
    assert vm.io.disps == [[1, 2, 3], [1, 2, 3]]


def test_list_subscript_digits_0_through_9():
    vm = run('{10}->L₀\n{11}->L₁\n{16}->L₆\n{19}->L₉\nDisp L₀\nDisp L₁\nDisp L₆\nDisp L₉')
    assert vm.io.disps == [[10], [11], [16], [19]]


def test_list_copy_is_independent():
    vm = run('{1}->l1\nl1->l2\n2->l2(1)\nDisp l1\nDisp l2')
    assert vm.io.disps == [[1], [2]]


def test_dim_get_for_list():
    vm = run('{1,2,3}->lTEST\nDisp dim(lTEST)')
    assert vm.io.disps == [3]


def test_dim_set_for_list_pads_with_zeros():
    vm = run('{1}->l1\n3->dim(l1)\nDisp l1')
    assert vm.io.disps == [[1, 0, 0]]


def test_list_store_beyond_length_pads_with_zeros():
    vm = run('{1,2}->l1\n5->l1(5)\nDisp l1')
    assert vm.io.disps == [[1, 2, 0, 0, 5]]


def test_matrix_store_and_index():
    # Disp formats matrices as strings (see tokens.Disp.format_matrix)
    vm = run('[[1,2,3,4]]->[A]\nDisp [A]\n2->[A](1,1)\nDisp [A]')
    assert vm.io.disps == ['[[1, 2, 3, 4]]', '[[2, 2, 3, 4]]']


def test_dim_get_for_matrix():
    vm = run('[[1,2,3,4]]->[A]\nDisp dim([A])')
    assert vm.io.disps == [[1, 4]]


def test_dim_set_for_matrix():
    vm = run('[[1,2,3,4]]->[A]\n{1,1}->dim([A])\nDisp dim([A])\nDisp [A]')
    assert vm.io.disps == [[1, 1], '[[1]]']


def test_delvar_resets_real_variable():
    vm = run('5->A\nDelVar A\nDisp A')
    assert vm.io.disps == [0]


def test_delvar_resets_string_variable():
    vm = run('"hello"->Str0\nDelVar Str0\nDisp Str0')
    assert vm.io.disps == ['']


def test_delvar_resets_list():
    vm = run('{1,2,3}->lTEST\nDelVar lTEST\nDisp lTEST')
    assert vm.io.disps == [[]]


def test_delvar_chaining():
    vm = run('1->A\n2->B\n3->C\nDelVar ADelVar BDelVar C\nDisp A\nDisp B\nDisp C')
    assert vm.io.disps == [0, 0, 0]


def test_delvar_on_unset_variable_is_safe():
    vm = run('DelVar A\nDisp A')
    assert vm.io.disps == [0]


def test_archive_is_a_noop():
    vm = run('5->A\nArchive A\nDisp A')
    assert vm.io.disps == [5]


def test_unarchive_is_a_noop():
    vm = run('5->A\nUnArchive A\nDisp A')
    assert vm.io.disps == [5]


def test_archive_and_unarchive_without_argument_are_safe():
    vm = run('Archive\nUnArchive\nDisp 1')
    assert vm.io.disps == [1]


def test_sorta_single_list():
    vm = run('{3,1,2}->lA\nSortA(lA)\nDisp lA')
    assert vm.io.disps == [[1, 2, 3]]


def test_sortd_single_list():
    vm = run('{1,3,2}->lA\nSortD(lA)\nDisp lA')
    assert vm.io.disps == [[3, 2, 1]]


def test_sorta_with_dependent_list():
    vm = run('{3,1,2}->lKEY\n{30,10,20}->lDEP\nSortA(lKEY,lDEP)\nDisp lKEY\nDisp lDEP')
    assert vm.io.disps == [[1, 2, 3], [10, 20, 30]]


def test_sortd_with_dependent_list():
    vm = run('{1,3,2}->lKEY\n{10,30,20}->lDEP\nSortD(lKEY,lDEP)\nDisp lKEY\nDisp lDEP')
    assert vm.io.disps == [[3, 2, 1], [30, 20, 10]]


def test_deltalist_consecutive_differences():
    vm = run('{1,4,9,16}->lA\nDisp ΔList(lA)')
    assert vm.io.disps == [[3, 5, 7]]


def test_deltalist_with_negatives():
    vm = run('{5,3,1}->lA\nDisp ΔList(lA)')
    assert vm.io.disps == [[-2, -2]]


def test_deltalist_single_element_returns_empty():
    vm = run('{7}->lA\nDisp ΔList(lA)')
    assert vm.io.disps == [[]]


def test_cumsum_basic():
    vm = run('{1,2,3,4}->lA\nDisp cumSum(lA)')
    assert vm.io.disps == [[1, 3, 6, 10]]


def test_cumsum_single_element():
    vm = run('{5}->lA\nDisp cumSum(lA)')
    assert vm.io.disps == [[5]]


def test_cumsum_deltalist_removes_first_element():
    # ΔList(cumSum(∟L→∟L is the TI-BASIC idiom for removing the first element
    vm = run('{10,20,30,40}->lA\nΔList(cumSum(lA))->lA\nDisp lA')
    assert vm.io.disps == [[20, 30, 40]]


def test_prod_whole_list():
    vm = run('{1,2,3,4,5}->lA\nDisp prod(lA)')
    assert vm.io.disps == [120]


def test_prod_with_start_only():
    vm = run('{1,2,3,4,5}->lA\nDisp prod(lA,3)')
    assert vm.io.disps == [60]


def test_prod_with_start_and_end():
    vm = run('{1,2,3,4,5}->lA\nDisp prod(lA,2,4)')
    assert vm.io.disps == [24]


def test_prod_of_list_literal():
    vm = run('Disp prod({2,3,4})')
    assert vm.io.disps == [24]


def test_clrlist_single_list():
    vm = run('{1,2,3}->lA\nClrList lA\nDisp lA')
    assert vm.io.disps == [[]]


def test_clrlist_multiple_lists():
    vm = run('{1,2,3}->lA\n{4,5}->lB\nClrList lA,lB\nDisp lA\nDisp lB')
    assert vm.io.disps == [[], []]


def test_clrlist_dim_returns_zero_after_clear():
    vm = run('{1,2,3}->lA\nClrList lA\nDisp dim(lA)')
    assert vm.io.disps == [0]


def test_clralllists_clears_every_list():
    vm = run('{1,2,3}->lA\n{4,5}->lB\nClrAllLists\nDisp lA\nDisp lB')
    assert vm.io.disps == [[], []]


def test_clralllists_without_lists_is_safe():
    vm = run('ClrAllLists\nDisp 1')
    assert vm.io.disps == [1]


def test_sorta_deck_shuffle_permutes_deck():
    # The deck shuffle pattern from the TI-BASIC guide:
    # seq(X,X,1,5->lDECK, rand(5->lRND, SortA(lRND,lDECK)
    vm = run('seq(X,X,1,5)->lDECK\nrand(5)->lRND\nSortA(lRND,lDECK)\nDisp lDECK')
    deck = vm.io.disps[0]
    assert sorted(deck) == [1, 2, 3, 4, 5]
