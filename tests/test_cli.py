"""Tests for pitybas.cli.main, which previously had no dedicated test
coverage at all. Writing these caught a real bug: the --ast branch called
a bare `print_ast(vm)` (no such name exists in cli.py -- it's a method,
`vm.print_ast()`), so `pb -a file.bas` always raised NameError. Fixed
alongside these tests.
"""
import io as std_io

import pytest

from pitybas import cli
from pitybas.common import ExecutionError


class FakeVM:
    """Stands in for an Interpreter so we can drive cli.main's branches
    (verbose/ast/stacktrace/error-handling) without actually parsing or
    running a program."""

    def __init__(self, execute_raises=None, line=3):
        self.execute_raises = execute_raises
        self.line = line
        self.print_tokens_calls = 0
        self.print_ast_calls = 0
        self.stacktrace_calls = []

    def execute(self):
        if self.execute_raises is not None:
            raise self.execute_raises

    def print_tokens(self):
        self.print_tokens_calls += 1

    def print_ast(self):
        self.print_ast_calls += 1

    def print_stacktrace(self, vardump=False):
        self.stacktrace_calls.append(vardump)


def patch_from_file(monkeypatch, vm, captured=None):
    def stub(filename, *args, **kwargs):
        if captured is not None:
            captured['filename'] = filename
            captured['kwargs'] = kwargs
        return vm

    monkeypatch.setattr(cli.Interpreter, 'from_file', stub)


def test_too_many_positional_args_prints_usage_and_exits_1(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(['one.bas', 'two.bas'])

    assert exc_info.value.code == 1
    assert 'Usage: pb' in capsys.readouterr().out


def test_no_filename_starts_repl_with_welcome_message(monkeypatch, capsys):
    # empty stdin means the REPL's input() immediately hits EOF and the
    # program terminates cleanly instead of blocking on real stdin.
    monkeypatch.setattr('sys.stdin', std_io.StringIO(''))

    cli.main([])

    assert 'Welcome to pitybas' in capsys.readouterr().out


def test_filename_runs_via_interpreter_from_file(monkeypatch, capsys):
    vm = FakeVM()
    captured = {}
    patch_from_file(monkeypatch, vm, captured)

    cli.main(['prog.bas'])

    assert captured['filename'] == 'prog.bas'
    assert vm.print_tokens_calls == 0


def test_io_option_selects_vt100_backend(monkeypatch):
    from pitybas.io.vt100 import IO as vt100

    vm = FakeVM()
    captured = {}
    patch_from_file(monkeypatch, vm, captured)

    cli.main(['-i', 'vt100', 'prog.bas'])

    assert captured['kwargs']['io'] is vt100


def test_io_option_defaults_to_none_for_unknown_value(monkeypatch):
    vm = FakeVM()
    captured = {}
    patch_from_file(monkeypatch, vm, captured)

    cli.main(['prog.bas'])

    assert captured['kwargs']['io'] is None


def test_verbose_with_filename_prints_tokens_and_running_banner(monkeypatch, capsys):
    vm = FakeVM()
    patch_from_file(monkeypatch, vm)

    cli.main(['-v', 'prog.bas'])

    assert vm.print_tokens_calls == 1
    assert '-===[ Running prog.bas ]===-' in capsys.readouterr().out


def test_verbose_without_filename_does_not_print_running_banner(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', std_io.StringIO(''))

    cli.main(['-v'])

    assert 'Running' not in capsys.readouterr().out


def test_ast_flag_prints_ast_and_exits_0(monkeypatch, capsys):
    vm = FakeVM()
    patch_from_file(monkeypatch, vm)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(['-a', 'prog.bas'])

    assert exc_info.value.code == 0
    assert vm.print_ast_calls == 1


def test_ast_flag_end_to_end_with_real_interpreter(tmp_path, capsys):
    # regression test for the print_ast(vm) NameError bug: run a real
    # program through the real Interpreter rather than a FakeVM.
    path = tmp_path / 'prog.bas'
    path.write_text('Disp 1\nDisp 2\n')

    with pytest.raises(SystemExit) as exc_info:
        cli.main(['-a', str(path)])

    assert exc_info.value.code == 0
    assert '0:' in capsys.readouterr().out


def test_stacktrace_flag_prints_stacktrace_after_successful_execute(monkeypatch):
    vm = FakeVM()
    patch_from_file(monkeypatch, vm)

    cli.main(['-s', 'prog.bas'])

    assert vm.stacktrace_calls == [None]


def test_keyboard_interrupt_during_execute_prints_stacktrace(monkeypatch, capsys):
    vm = FakeVM(execute_raises=KeyboardInterrupt())
    patch_from_file(monkeypatch, vm)

    cli.main(['prog.bas'])

    assert vm.stacktrace_calls == [None]


def test_pitybas_error_during_execute_prints_message_not_traceback(monkeypatch, capsys):
    vm = FakeVM(execute_raises=ExecutionError('boom'))
    patch_from_file(monkeypatch, vm)

    cli.main(['prog.bas'])

    out = capsys.readouterr().out
    assert 'ExecutionError on line 3:' in out
    assert 'boom' in out
    assert 'Python traceback' not in out
    assert vm.stacktrace_calls == [None]


def test_unexpected_exception_during_execute_prints_python_traceback(monkeypatch, capsys):
    vm = FakeVM(execute_raises=ValueError('unexpected'))
    patch_from_file(monkeypatch, vm)

    cli.main(['prog.bas'])

    out = capsys.readouterr().out
    assert 'ValueError on line 3:' in out
    assert '-===[ Python traceback ]===-' in out
    assert 'ValueError: unexpected' in out
