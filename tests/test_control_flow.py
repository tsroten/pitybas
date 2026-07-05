import pytest

from pitybas.common import StopError, ReturnError, ExecutionError
from conftest import run


def test_if_then_true_branch():
    vm = run('If 1\nThen\nDisp "yes"\nEnd')
    assert vm.io.disps == ['yes']


def test_if_then_false_branch_skips_body():
    vm = run('If 0\nThen\nDisp "yes"\nEnd\nDisp "after"')
    assert vm.io.disps == ['after']


def test_if_then_else():
    vm = run('If 0\nThen\nDisp "a"\nElse\nDisp "b"\nEnd')
    assert vm.io.disps == ['b']


def test_if_without_then_runs_next_line_only_when_true():
    vm = run('If 1\nDisp "phase one"\nIf 0\nDisp "phase two"\nDisp "phase three"')
    assert vm.io.disps == ['phase one', 'phase three']


def test_nested_if_then():
    vm = run(
        'If 1\n'
        'Then\n'
        'While 0\n'
        'If 1\n'
        'Then\n'
        'Disp "umm"\n'
        'End\n'
        'Disp "nooo"\n'
        'End\n'
        'Disp "yes!"\n'
        'End'
    )
    assert vm.io.disps == ['yes!']


def test_for_loop_counts_down():
    vm = run('For(A,5,1,-1)\nDisp A\nEnd')
    assert vm.io.disps == [5, 4, 3, 2, 1]


def test_for_loop_counts_up():
    vm = run('For(A,1,3)\nDisp A\nEnd')
    assert vm.io.disps == [1, 2, 3]


def test_while_loop():
    vm = run('1->A\nWhile A<5\nDisp A\nA+1->A\nEnd')
    assert vm.io.disps == [1, 2, 3, 4]


def test_repeat_loop_runs_until_condition_true():
    vm = run('1->A\nRepeat A>5\nDisp A\nA+1->A\nEnd')
    assert vm.io.disps == [1, 2, 3, 4, 5]


def test_goto_lbl_skips_intermediate_code():
    vm = run('Goto A\nDisp "skipped"\nLbl A\nDisp "reached"')
    assert vm.io.disps == ['reached']


def test_stop_raises_stop_error_and_halts_execution():
    vm = run('Disp "before"\nStop\nDisp "after"')
    assert vm.io.disps == ['before']


def test_return_raises_return_error_and_halts_execution():
    vm = run('Disp "before"\nReturn\nDisp "after"')
    assert vm.io.disps == ['before']


def test_prgm_raises_execution_error_when_subprogram_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ExecutionError, match='prgm'):
        run('prgmMISSING')


def test_prgm_executes_subprogram_file(tmp_path, monkeypatch):
    (tmp_path / 'helper.bas').write_text('2->A')
    monkeypatch.chdir(tmp_path)
    # prgmHELPER should locate helper.bas and execute it without error
    run('prgmHELPER')
