"""Tests for Interpreter.print_ast/print_tokens/print_stacktrace. These
debugging helpers (used by `pb -a`/`-v`/`-s`) previously had no test
coverage at all.

Writing test_print_ast_without_highlight_does_not_crash caught a real
bug: print_ast()'s default `highlight=None` was compared with
`highlight - 1`, so calling it with no highlight argument (as `pb -a`
does) raised TypeError unconditionally. Fixed by skipping the highlight
comparison when highlight is None.
"""

from conftest import make_vm
from pitybas.interpret import Interpreter
from pitybas.io.simple import IO as SimpleIO


def test_print_ast_without_highlight_does_not_crash(capsys):
    vm = make_vm("Disp 1\nDisp 2")

    vm.print_ast()

    out = capsys.readouterr().out
    assert "0:" in out
    assert "1:" in out
    assert ">>>>" not in out


def test_print_ast_highlights_requested_line(capsys):
    vm = make_vm("Disp 1\nDisp 2\nDisp 3")

    vm.print_ast(highlight=2)

    lines = capsys.readouterr().out.splitlines()
    assert lines[1].startswith(">>>>")
    assert not lines[0].startswith(">>>>")
    assert not lines[2].startswith(">>>>")


def test_print_ast_respects_start_and_end_bounds(capsys):
    vm = make_vm("Disp 1\nDisp 2\nDisp 3\nDisp 4")

    vm.print_ast(start=1, end=3)

    out = capsys.readouterr().out
    assert "0:" not in out
    assert "1:" in out
    assert "2:" in out
    assert "3:" not in out


def test_print_tokens_prints_one_line_per_code_line(capsys):
    vm = make_vm("Disp 1\nDisp 2")

    vm.print_tokens()

    lines = capsys.readouterr().out.splitlines()
    # code lines plus the appended EOF line
    assert len(lines) == 3
    assert "Disp" in lines[0]


def test_print_stacktrace_after_execution_shows_history_and_code(capsys):
    vm = make_vm("Disp 1\nDisp 2")
    vm.execute()

    vm.print_stacktrace()

    out = capsys.readouterr().out
    assert "-===[ Stacktrace ]===-" in out
    assert "-===[ Code (row" in out


def test_print_stacktrace_vardump_shows_variables(capsys):
    vm = make_vm("42->A")
    vm.execute()

    vm.print_stacktrace(vardump=True)

    out = capsys.readouterr().out
    assert "-===[ Variable Dump ]===-" in out
    assert "'A': 42" in out


def test_print_stacktrace_with_name_prints_dumping_header(tmp_path, capsys):
    path = tmp_path / "prog.bas"
    path.write_text("Disp 1")
    vm = Interpreter.from_file(str(path), io=SimpleIO)
    vm.execute()

    vm.print_stacktrace()

    assert "-===[ Dumping prog.bas ]===-" in capsys.readouterr().out


def test_print_stacktrace_without_history_omits_stacktrace_section(capsys):
    vm = make_vm("Disp 1")

    vm.print_stacktrace()

    out = capsys.readouterr().out
    assert "-===[ Stacktrace ]===-" not in out
    assert "-===[ Code (row" in out
