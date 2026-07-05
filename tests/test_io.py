from conftest import run


def test_disp_multiple_values_via_comma():
    vm = run('Disp 1, 2, "three"')
    assert vm.io.disps == [1, 2, 'three']


def test_disp_with_no_argument_prints_blank():
    vm = run('Disp')
    assert vm.io.disps == ['']


def test_print_joins_multiple_values_with_commas():
    vm = run('Print 1, 2, 3')
    assert vm.io.disps == ['1, 2, 3']


def test_clrhome_calls_clear():
    vm = run('ClrHome')
    assert vm.io.clears == 1


def test_output_writes_row_col_message():
    vm = run('Output(1, 2, "hi")')
    assert vm.io.outputs == [(1, 2, 'hi')]


def test_prompt_reads_input_and_stores_variable():
    vm = run('Prompt A\nDisp A', inputs=['42'])
    assert vm.io.disps == [42]


def test_prompt_multiple_variables():
    vm = run('Prompt A, B\nDisp A\nDisp B', inputs=['3', '4'])
    assert vm.io.disps == [3, 4]


def test_input_with_message_string_variable():
    vm = run('Input "name?", Str0\nDisp Str0', inputs=['bob'])
    assert vm.io.disps == ['bob']


def test_input_without_message():
    vm = run('Input A\nDisp A', inputs=['7'])
    assert vm.io.disps == [7]


def test_pause_displays_message():
    vm = run('Pause "hold on"', inputs=[''])
    assert vm.io.disps == ['hold on']


def test_fixed_precision_rounds_display():
    vm = run('Fix 2\nDisp 3.14159')
    assert vm.io.disps == [3.14]


def test_float_resets_fixed_precision():
    vm = run('Fix 2\nFloat\nDisp 3.14159')
    assert vm.io.disps == [3.14159]
