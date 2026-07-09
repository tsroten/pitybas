"""Tests for pitybas.io.scripted.ScriptedIO."""

import pytest

from pitybas.interpret import Interpreter
from pitybas.io.scripted import ScriptedIO


@pytest.fixture
def vm():
    return Interpreter.from_string('')


def test_scripted_io_is_importable_from_pitybas_io():
    from pitybas.io import ScriptedIO as _ScriptedIO
    assert _ScriptedIO is ScriptedIO


def test_getkey_returns_from_keys_list(vm):
    io = ScriptedIO(vm, keys=[45, 25])
    assert io.getkey() == 45
    assert io.getkey() == 25


def test_getkey_returns_zero_when_keys_exhausted(vm):
    io = ScriptedIO(vm, keys=[10])
    io.getkey()  # consume the only key
    assert io.getkey() == 0


def test_getkey_returns_zero_with_no_keys(vm):
    io = ScriptedIO(vm)
    assert io.getkey() == 0


def test_menu_selects_first_option_via_inputs(vm):
    io = ScriptedIO(vm, inputs=['1'])
    menu = [('TITLE', [('OPT1', 'A'), ('OPT2', 'B')])]
    assert io.menu(menu) == 'A'


def test_menu_selects_second_option_via_inputs(vm):
    io = ScriptedIO(vm, inputs=['2'])
    menu = [('TITLE', [('OPT1', 'A'), ('OPT2', 'B')])]
    assert io.menu(menu) == 'B'


def test_menu_consumes_from_inputs_queue(vm):
    io = ScriptedIO(vm, inputs=['2', '1'])
    menu = [('TITLE', [('OPT1', 'A'), ('OPT2', 'B')])]
    io.menu(menu)
    # first choice consumed; remaining inputs still usable
    assert io.inputs == ['1']


def test_menu_across_multiple_groups(vm):
    io = ScriptedIO(vm, inputs=['3'])
    menu = [('G1', [('OPT1', 'A'), ('OPT2', 'B')]), ('G2', [('OPT3', 'C')])]
    assert io.menu(menu) == 'C'


def test_clear_increments_counter(vm):
    io = ScriptedIO(vm)
    io.clear()
    io.clear()
    assert io.clears == 2


def test_disp_records_message(vm):
    io = ScriptedIO(vm)
    io.disp('hello')
    io.disp(42)
    assert io.disps == ['hello', 42]


def test_output_records_row_col_msg(vm):
    io = ScriptedIO(vm)
    io.output(1, 2, 'hi')
    assert io.outputs == [(1, 2, 'hi')]


def test_scripted_io_drives_full_program():
    """End-to-end: ScriptedIO drives Input + Disp through the interpreter."""
    vm = Interpreter.from_string(
        'Input A\nDisp A*2',
        io=lambda vm: ScriptedIO(vm, inputs=['21']),
    )
    vm.execute()
    assert vm.io.disps == [42]


def test_scripted_io_drives_menu_program():
    """End-to-end: ScriptedIO selects menu option 1 and reaches its label."""
    vm = Interpreter.from_string(
        'Menu("TITLE","OPT1",A,"OPT2",B)\nDisp "no\nLbl A\nDisp "yes',
        io=lambda vm: ScriptedIO(vm, inputs=['1']),
    )
    vm.execute()
    assert vm.io.disps == ['yes']
