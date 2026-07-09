"""Tests for pitybas.io.simple.IO, the default (non-vt100) IO backend.
Existing tests only ever drive programs through ScriptedIO (see
pitybas.io.scripted.ScriptedIO), so this real backend -- which talks to actual
print()/input() -- had no direct coverage at all.
"""
import pytest

from pitybas.interpret import Interpreter
from pitybas.io.simple import IO


@pytest.fixture
def io_obj():
    vm = Interpreter.from_string('')
    return IO(vm)


def test_clear_prints_separator(io_obj, capsys):
    io_obj.clear()

    assert capsys.readouterr().out == '-' * 16 + '\n'


def test_output_prints_message(io_obj, capsys):
    io_obj.output(1, 2, 'hi')

    assert capsys.readouterr().out == 'hi\n'


def test_disp_prints_message(io_obj, capsys):
    io_obj.disp('hello')

    assert capsys.readouterr().out == 'hello\n'


def test_disp_defaults_to_blank_line(io_obj, capsys):
    io_obj.disp()

    assert capsys.readouterr().out == '\n'


def test_getkey_is_not_implemented(io_obj):
    with pytest.raises(NotImplementedError):
        io_obj.getkey()


def test_input_parses_typed_expression(io_obj, monkeypatch, capsys):
    monkeypatch.setattr('builtins.input', lambda: '2+3')

    assert io_obj.input('sum?') == 5
    assert capsys.readouterr().out == 'sum? '


def test_input_with_no_message_prints_nothing_before_reading(io_obj, monkeypatch, capsys):
    monkeypatch.setattr('builtins.input', lambda: '7')

    assert io_obj.input('') == 7
    assert capsys.readouterr().out == ''


def test_input_returns_raw_string_when_is_str(io_obj, monkeypatch):
    monkeypatch.setattr('builtins.input', lambda: 'hello world')

    assert io_obj.input('name?', is_str=True) == 'hello world'


def test_input_reprompts_on_parse_error(io_obj, monkeypatch, capsys):
    responses = iter(['@@@', '5'])
    monkeypatch.setattr('builtins.input', lambda: next(responses))

    assert io_obj.input('n?') == 5
    assert 'ERR:DATA' in capsys.readouterr().out


def test_pause_with_message_displays_then_waits_for_enter(io_obj, monkeypatch, capsys):
    monkeypatch.setattr('builtins.input', lambda: '')

    io_obj.pause('hold on')

    out = capsys.readouterr().out
    assert 'hold on' in out
    assert '[press enter]' in out


def test_pause_without_message_only_waits_for_enter(io_obj, monkeypatch, capsys):
    monkeypatch.setattr('builtins.input', lambda: '')

    io_obj.pause()

    assert capsys.readouterr().out == '[press enter] '


def test_menu_returns_label_for_valid_choice(io_obj, monkeypatch, capsys):
    # title/desc arrive as plain, already-evaluated display strings (see
    # tokens.Menu.run); only the label stays a raw token/value for Goto.
    menu = (('pick one', [('first', 'LBL1'), ('second', 'LBL2')]),)

    monkeypatch.setattr('builtins.input', lambda: '2')

    assert io_obj.menu(menu) == 'LBL2'
    assert '-[ pick one ]-' in capsys.readouterr().out


def test_menu_reprompts_on_invalid_choice(io_obj, monkeypatch, capsys):
    menu = (('t', [('only', 'LBL')]),)

    responses = iter(['nope', '99', '1'])
    monkeypatch.setattr('builtins.input', lambda: next(responses))

    assert io_obj.menu(menu) == 'LBL'
    assert capsys.readouterr().out.count('invalid choice') == 2
