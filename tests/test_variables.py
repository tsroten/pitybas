from conftest import run


def test_simple_variable_store_and_get():
    vm = run('5->A\nDisp A')
    assert vm.io.disps == [5]
    assert vm.vars['A'] == 5


def test_variable_defaults_to_zero():
    vm = run('Disp A')
    assert vm.io.disps == [0]


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
