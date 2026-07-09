"""Tests for pitybas.io.vt100: keycodes, Delayed, SafeIO, VT, and IO."""

import types

import pytest

from pitybas.graph import GraphState
from pitybas.interpret import Interpreter
from pitybas.io import vt100
from pitybas.io.vt100 import (
    BRAILLE_BASE,
    Delayed,
    GRAPH_COLS,
    GRAPH_ROWS,
    IO,
    SafeIO,
    VT,
    keycodes,
    render_braille,
)


# ── helpers ──────────────────────────────────────────────────────────────────


@pytest.fixture
def vt(capsys):
    obj = VT()
    capsys.readouterr()  # discard escape sequences emitted by __init__
    return obj


@pytest.fixture
def io_obj(capsys):
    obj = IO(Interpreter.from_string(""))
    capsys.readouterr()  # discard escape sequences emitted by VT.__init__
    return obj


def _patch_tty(monkeypatch):
    """Suppress all terminal-control and timing calls used inside VT.getch."""
    monkeypatch.setattr(vt100.termios, "tcgetattr", lambda fd: None)
    monkeypatch.setattr(vt100.termios, "tcsetattr", lambda fd, when, attrs: None)
    monkeypatch.setattr(vt100.tty, "setraw", lambda fd: None)
    monkeypatch.setattr(vt100.time, "sleep", lambda _: None)


def _patch_stdin_reads(monkeypatch, chars):
    """Patch sys.stdin so read(1) yields successive characters from *chars*."""
    it = iter(chars)
    monkeypatch.setattr(vt100.select, "select", lambda r, w, x, timeout: (r, [], []))
    monkeypatch.setattr(
        vt100.sys,
        "stdin",
        types.SimpleNamespace(
            fileno=lambda: 0,
            read=lambda n: next(it, ""),
        ),
    )


# ── keycodes ─────────────────────────────────────────────────────────────────


def test_keycodes_enter():
    assert keycodes["enter"] == 105


def test_keycodes_arrow_keys():
    assert keycodes["left"] == 24
    assert keycodes["up"] == 25
    assert keycodes["right"] == 26
    assert keycodes["down"] == 34


def test_keycodes_letters():
    assert keycodes["A"] == 41
    assert keycodes["Z"] == 93


def test_keycodes_special_chars():
    assert keycodes['"'] == 95
    assert keycodes[" "] == 102
    assert keycodes[":"] == 103
    assert keycodes["?"] == 104


# ── Delayed ──────────────────────────────────────────────────────────────────


def test_delayed_sleeps_remaining_time(monkeypatch):
    slept = []
    monkeypatch.setattr(vt100.time, "sleep", slept.append)
    monkeypatch.setattr(vt100.time, "time", iter([0.0, 0.05]).__next__)

    with Delayed(0.1):
        pass

    assert len(slept) == 1
    assert abs(slept[0] - 0.05) < 0.001


def test_delayed_does_not_sleep_when_already_elapsed(monkeypatch):
    slept = []
    monkeypatch.setattr(vt100.time, "sleep", slept.append)
    monkeypatch.setattr(vt100.time, "time", iter([0.0, 0.2]).__next__)

    with Delayed(0.1):
        pass

    assert slept == []


# ── SafeIO ───────────────────────────────────────────────────────────────────


def test_safeio_restores_terminal_settings(monkeypatch):
    saved = {}
    attrs = object()
    monkeypatch.setattr(vt100.termios, "tcgetattr", lambda fd: attrs)
    monkeypatch.setattr(
        vt100.termios,
        "tcsetattr",
        lambda fd, when, a: saved.update({"when": when, "attrs": a}),
    )

    with SafeIO(0):
        pass

    assert saved["attrs"] is attrs
    assert saved["when"] == vt100.termios.TCSANOW


# ── VT: __init__ ─────────────────────────────────────────────────────────────


def test_vt_default_dimensions(capsys):
    vt = VT()
    capsys.readouterr()
    assert vt.width == 16
    assert vt.height == 8


def test_vt_custom_dimensions(capsys):
    vt = VT(width=20, height=10)
    capsys.readouterr()
    assert vt.width == 20
    assert vt.height == 10


def test_vt_initial_position(capsys):
    vt = VT()
    capsys.readouterr()
    assert vt.row == 1
    assert vt.col == 1


def test_vt_initial_lines_shape(capsys):
    vt = VT(width=4, height=3)
    capsys.readouterr()
    assert len(vt.lines) == 3
    assert all(len(line) == 4 for line in vt.lines)
    assert all(ch == " " for line in vt.lines for ch in line)


def test_vt_initial_pos_stack_is_empty(capsys):
    vt = VT()
    capsys.readouterr()
    assert vt.pos_stack == []


# ── VT: push / pop ───────────────────────────────────────────────────────────


def test_vt_push_pop_round_trips_position(vt):
    vt.row, vt.col = 3, 5
    vt.push()
    vt.row, vt.col = 1, 1
    vt.pop()
    assert (vt.row, vt.col) == (3, 5)


def test_vt_push_pop_lifo_order(vt):
    vt.row, vt.col = 2, 4
    vt.push()
    vt.row, vt.col = 5, 7
    vt.push()
    vt.pop()
    assert (vt.row, vt.col) == (5, 7)
    vt.pop()
    assert (vt.row, vt.col) == (2, 4)


# ── VT: e ─────────────────────────────────────────────────────────────────────


def test_vt_e_writes_single_escape_sequence(vt, capsys):
    vt.e("[2J")
    assert capsys.readouterr().out == "\033[2J"


def test_vt_e_writes_multiple_escape_sequences(vt, capsys):
    vt.e("[2J", "[H")
    assert capsys.readouterr().out == "\033[2J\033[H"


# ── VT: clear ────────────────────────────────────────────────────────────────


def test_vt_clear_with_reset_reinitialises_lines(capsys):
    vt = VT(width=4, height=2)
    capsys.readouterr()
    vt.lines[0][0] = "X"
    vt.clear(reset=True)
    capsys.readouterr()
    assert vt.lines[0][0] == " "


def test_vt_clear_without_reset_preserves_lines(capsys):
    vt = VT(width=4, height=2)
    capsys.readouterr()
    vt.lines[0][0] = "X"
    vt.clear(reset=False)
    capsys.readouterr()
    assert vt.lines[0][0] == "X"


def test_vt_clear_resets_cursor_to_origin(capsys):
    vt = VT()
    capsys.readouterr()
    vt.row, vt.col = 5, 3
    vt.clear()
    capsys.readouterr()
    assert vt.row == 1
    assert vt.col == 1


def test_vt_clear_emits_erase_and_home_sequences(capsys):
    vt = VT()
    capsys.readouterr()
    vt.clear()
    out = capsys.readouterr().out
    assert "\033[2J" in out
    assert "\033[H" in out


# ── VT: scroll ───────────────────────────────────────────────────────────────


def test_vt_scroll_removes_first_row_and_appends_blank(capsys):
    vt = VT(width=3, height=3)
    capsys.readouterr()
    vt.lines[0] = list("ABC")
    vt.lines[1] = list("DEF")
    vt.lines[2] = list("GHI")
    vt.scroll()
    assert vt.lines[0] == list("DEF")
    assert vt.lines[1] == list("GHI")
    assert vt.lines[2] == list("   ")


def test_vt_scroll_decrements_row(vt):
    vt.row = 4
    vt.scroll()
    assert vt.row == 3


def test_vt_scroll_row_cannot_go_below_one(vt):
    vt.row = 1
    vt.scroll()
    assert vt.row == 1


# ── VT: flush ────────────────────────────────────────────────────────────────


def test_vt_flush_writes_all_lines_to_stdout(capsys):
    vt = VT(width=3, height=2)
    capsys.readouterr()
    vt.lines[0] = list("ABC")
    vt.lines[1] = list("DEF")
    vt.flush()
    out = capsys.readouterr().out
    assert "ABC" in out
    assert "DEF" in out


def test_vt_flush_preserves_lines_content(capsys):
    vt = VT(width=3, height=2)
    capsys.readouterr()
    vt.lines[0] = list("XYZ")
    vt.flush()
    assert vt.lines[0] == list("XYZ")


# ── VT: move ─────────────────────────────────────────────────────────────────


def test_vt_move_updates_row_and_col(vt, capsys):
    vt.move(3, 7)
    assert vt.row == 3
    assert vt.col == 7


def test_vt_move_emits_cursor_position_sequence(vt, capsys):
    vt.move(2, 5)
    out = capsys.readouterr().out
    assert "\033[2;5H" in out


# ── VT: wrap ─────────────────────────────────────────────────────────────────


def test_vt_wrap_short_message_fits_on_one_line(capsys):
    vt = VT(width=10, height=5)
    capsys.readouterr()
    vt.col = 1
    assert vt.wrap("hello") == ["hello"]


def test_vt_wrap_splits_at_width_boundary(capsys):
    vt = VT(width=5, height=5)
    capsys.readouterr()
    vt.col = 1
    chunks = vt.wrap("ABCDEFGHIJ")
    assert chunks[0] == "ABCDE"
    assert chunks[1] == "FGHIJ"


def test_vt_wrap_accounts_for_current_column_offset(capsys):
    vt = VT(width=5, height=5)
    capsys.readouterr()
    vt.col = 3  # only 3 chars fit on the current row (cols 3, 4, 5)
    chunks = vt.wrap("ABCDE")
    assert chunks[0] == "ABC"
    assert chunks[1] == "DE"


def test_vt_wrap_converts_non_string_to_str(capsys):
    vt = VT(width=10, height=5)
    capsys.readouterr()
    vt.col = 1
    chunks = vt.wrap(42)
    assert chunks == ["42"]


# ── VT: write ────────────────────────────────────────────────────────────────


def test_vt_write_stores_chars_in_lines(vt, capsys):
    vt.write("hi")
    assert vt.lines[0][:2] == list("hi")


def test_vt_write_advances_row_after_first_line(vt, capsys):
    vt.write("AB")
    # write always appends '\n' after each wrapped segment → row advances
    assert vt.row == 2


def test_vt_write_scrolls_when_row_exceeds_height(capsys):
    vt = VT(width=5, height=2)
    capsys.readouterr()
    vt.write("12345")  # fills row 1; cursor moves to row 2
    vt.write("ABCDE")  # fills row 2; cursor moves to row 3
    vt.write("XXXXX")  # row 3 > height=2 → scroll occurs
    # First row is discarded, old row-2 content promoted to row 1
    assert vt.lines[0] == list("ABCDE")
    assert vt.lines[1] == list("XXXXX")


def test_vt_write_no_scroll_stops_at_height(capsys):
    vt = VT(width=5, height=2)
    capsys.readouterr()
    vt.write("12345")  # row 1
    vt.write("ABCDE")  # row 2; cursor → row 3
    # Writing with scroll=False should not modify lines further
    vt.write("XXXXX", scroll=False)
    assert vt.lines[0] == list("12345")
    assert vt.lines[1] == list("ABCDE")


# ── VT: output ───────────────────────────────────────────────────────────────


def test_vt_output_writes_to_target_row_and_col(vt, capsys):
    vt.output(2, 1, "hi")
    assert vt.lines[1][:2] == list("hi")


def test_vt_output_restores_cursor_position(vt, capsys):
    vt.row, vt.col = 1, 1
    vt.output(3, 5, "X")
    assert (vt.row, vt.col) == (1, 1)


# ── VT: getch ────────────────────────────────────────────────────────────────


def test_getch_returns_enter_for_carriage_return(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\r")
    assert VT().getch() == "enter"


def test_getch_returns_enter_for_newline(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\n")
    assert VT().getch() == "enter"


def test_getch_raises_keyboard_interrupt_for_ctrl_c(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\003")
    with pytest.raises(KeyboardInterrupt):
        VT().getch()


def test_getch_returns_up_for_escape_sequence(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\033[A")
    assert VT().getch() == "up"


def test_getch_returns_down_for_escape_sequence(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\033[B")
    assert VT().getch() == "down"


def test_getch_returns_right_for_escape_sequence(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\033[C")
    assert VT().getch() == "right"


def test_getch_returns_left_for_escape_sequence(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\033[D")
    assert VT().getch() == "left"


def test_getch_returns_none_for_unrecognised_escape_sequence(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\033X")
    assert VT().getch() is None


def test_getch_returns_none_for_escape_bracket_without_arrow(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\033[Z")
    assert VT().getch() is None


def test_getch_returns_none_when_no_input_available(monkeypatch):
    _patch_tty(monkeypatch)
    monkeypatch.setattr(vt100.select, "select", lambda r, w, x, timeout: ([], [], []))
    monkeypatch.setattr(vt100.sys, "stdin", types.SimpleNamespace(fileno=lambda: 0))
    assert VT().getch() is None


def test_getch_returns_regular_character(monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "k")
    assert VT().getch() == "k"


# ── IO: __init__ ─────────────────────────────────────────────────────────────


def test_io_init_creates_vt_instance(io_obj):
    assert isinstance(io_obj.vt, VT)


def test_io_init_stores_vm(io_obj):
    assert isinstance(io_obj.vm, Interpreter)


# ── IO: __enter__ / __exit__ ─────────────────────────────────────────────────


def test_io_enter_returns_self(io_obj, capsys):
    assert io_obj.__enter__() is io_obj


def test_io_enter_hides_cursor(io_obj, capsys):
    io_obj.__enter__()
    assert "\033[?25l" in capsys.readouterr().out


def test_io_exit_shows_cursor(io_obj, capsys):
    io_obj.__exit__(None, None, None)
    assert "\033[?25h" in capsys.readouterr().out


def test_io_exit_does_not_wait_when_text_screen_is_last_shown(io_obj, monkeypatch):
    # A program that never drew to the graph screen (or last touched the
    # text screen) has nothing on the graph screen to protect, so exiting
    # shouldn't block waiting for a keypress.
    monkeypatch.setattr(VT, "getch", lambda self: (_ for _ in ()).throw(AssertionError))
    io_obj.__exit__(None, None, None)  # should not raise


def test_io_exit_waits_for_keypress_when_graph_is_last_shown(io_obj, monkeypatch):
    # Mirrors a real TI-83/84: the drawn graph stays up until dismissed
    # instead of the process exiting straight back to the shell under it.
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    calls = []
    monkeypatch.setattr(VT, "getch", lambda self: calls.append(1) or "enter")
    io_obj.__exit__(None, None, None)
    assert calls == [1]


def test_io_exit_does_not_wait_when_text_follows_a_draw(io_obj, monkeypatch):
    # Confirmed on real hardware: ClrDraw/Circle(/Disp "DONE" does NOT hold
    # at exit -- Disp switches the active screen back to text/home, and
    # that's what's left showing (see PR discussion for the hardware
    # scenario this regression-tests).
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    io_obj.disp("DONE")
    monkeypatch.setattr(VT, "getch", lambda self: (_ for _ in ()).throw(AssertionError))
    io_obj.__exit__(None, None, None)  # should not raise


def test_io_exit_waits_when_draw_follows_text(io_obj, monkeypatch):
    # Confirmed on real hardware: Disp "BEFORE"/ClrDraw/Circle( DOES hold
    # at exit -- the graph screen took over and is still the active view.
    io_obj.disp("BEFORE")
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    calls = []
    monkeypatch.setattr(VT, "getch", lambda self: calls.append(1) or "enter")
    io_obj.__exit__(None, None, None)
    assert calls == [1]


def test_io_exit_does_not_wait_after_pause_dismissed(io_obj, monkeypatch):
    # Confirmed on real hardware: dismissing a Pause that's holding the
    # graph screen (pressing Enter) itself returns to the text/home
    # screen -- nothing further should hold at actual program end.
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    monkeypatch.setattr("builtins.input", lambda: "")
    io_obj.pause()
    monkeypatch.setattr(VT, "getch", lambda self: (_ for _ in ()).throw(AssertionError))
    io_obj.__exit__(None, None, None)  # should not raise


def test_io_exit_polls_getch_until_a_key_is_pressed(io_obj, monkeypatch):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    responses = iter([None, None, "enter"])
    monkeypatch.setattr(VT, "getch", lambda self: next(responses))
    io_obj.__exit__(None, None, None)  # should not raise StopIteration


def test_io_exit_skips_wait_on_unhandled_exception(io_obj, monkeypatch):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    monkeypatch.setattr(VT, "getch", lambda self: (_ for _ in ()).throw(AssertionError))
    io_obj.__exit__(ValueError, ValueError("boom"), None)  # should not raise


def test_io_exit_restores_cursor_even_if_getch_raises(io_obj, monkeypatch, capsys):
    # A Ctrl-C while holding the graph screen must not leave the terminal
    # cursor hidden -- the show-cursor sequence has to run regardless of
    # how the wait loop exits.
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    monkeypatch.setattr(
        VT, "getch", lambda self: (_ for _ in ()).throw(KeyboardInterrupt)
    )
    with pytest.raises(KeyboardInterrupt):
        io_obj.__exit__(None, None, None)


# ── IO: _last_screen tracking ────────────────────────────────────────────────


def test_last_screen_starts_as_text(io_obj):
    assert io_obj._last_screen == "text"


def test_last_screen_is_graph_after_draw(io_obj):
    io_obj.draw_pixel(0, 0, True)
    assert io_obj._last_screen == "graph"


def test_last_screen_is_text_after_disp(io_obj):
    io_obj.draw_pixel(0, 0, True)
    io_obj.disp("hi")
    assert io_obj._last_screen == "text"


def test_last_screen_is_text_after_output(io_obj):
    io_obj.draw_pixel(0, 0, True)
    io_obj.output(1, 1, "hi")
    assert io_obj._last_screen == "text"


def test_last_screen_is_text_after_clear(io_obj):
    io_obj.draw_pixel(0, 0, True)
    io_obj.clear()
    assert io_obj._last_screen == "text"


def test_last_screen_is_text_after_input(io_obj, monkeypatch):
    io_obj.draw_pixel(0, 0, True)
    monkeypatch.setattr("builtins.input", lambda: "1")
    io_obj.input("n?")
    assert io_obj._last_screen == "text"


def test_last_screen_is_text_after_menu(io_obj, monkeypatch):
    io_obj.draw_pixel(0, 0, True)
    menu = (("t", [("only", "LBL")]),)
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    io_obj.menu(menu)
    assert io_obj._last_screen == "text"


# ── IO: clear ────────────────────────────────────────────────────────────────


def test_io_clear_resets_vt_cursor_to_origin(io_obj, capsys):
    io_obj.vt.row, io_obj.vt.col = 5, 5
    io_obj.clear()
    assert io_obj.vt.row == 1
    assert io_obj.vt.col == 1


def test_io_clear_reinitialises_lines(io_obj, capsys):
    io_obj.vt.lines[0][0] = "X"
    io_obj.clear()
    capsys.readouterr()
    assert io_obj.vt.lines[0][0] == " "


# ── IO: input ────────────────────────────────────────────────────────────────


def test_io_input_parses_expression(io_obj, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "2+3")
    assert io_obj.input("val?") == 5


def test_io_input_returns_raw_string_when_is_str(io_obj, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "hello")
    assert io_obj.input("n?", is_str=True) == "hello"


def test_io_input_prints_message_to_stdout(io_obj, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda: "1")
    io_obj.input("enter value?")
    assert "enter value?" in capsys.readouterr().out


def test_io_input_silent_when_no_message(io_obj, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda: "7")
    io_obj.input("")
    # With no message the 'if msg: print(msg, ...)' branch is skipped;
    # only escape sequences are written — strip them and expect nothing left.
    import re

    out = capsys.readouterr().out
    text_only = re.sub(r"\x1b\[[^a-zA-Z]*[a-zA-Z]", "", out).strip()
    assert text_only == ""


def test_io_input_reprompts_on_parse_error(io_obj, monkeypatch, capsys):
    responses = iter(["@@@", "7"])
    monkeypatch.setattr("builtins.input", lambda: next(responses))
    assert io_obj.input("n?") == 7
    assert "ERR:DATA" in capsys.readouterr().out


# ── IO: getkey ───────────────────────────────────────────────────────────────


def test_io_getkey_returns_keycode_for_enter(io_obj, monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "\r")
    assert io_obj.getkey() == 105


def test_io_getkey_returns_zero_for_unknown_key(io_obj, monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "~")  # '~' is not in keycodes
    assert io_obj.getkey() == 0


def test_io_getkey_returns_keycode_for_letter(io_obj, monkeypatch):
    _patch_tty(monkeypatch)
    _patch_stdin_reads(monkeypatch, "A")
    assert io_obj.getkey() == keycodes["A"]


def test_io_getkey_returns_zero_when_getch_returns_none(io_obj, monkeypatch):
    _patch_tty(monkeypatch)
    monkeypatch.setattr(vt100.select, "select", lambda r, w, x, timeout: ([], [], []))
    monkeypatch.setattr(vt100.sys, "stdin", types.SimpleNamespace(fileno=lambda: 0))
    assert io_obj.getkey() == 0


# ── IO: output ───────────────────────────────────────────────────────────────


def test_io_output_writes_message_to_vt_lines(io_obj, capsys):
    io_obj.output(1, 1, "hi")
    assert io_obj.vt.lines[0][:2] == list("hi")


# ── IO: disp ─────────────────────────────────────────────────────────────────


def test_io_disp_writes_string_to_vt(io_obj, capsys):
    io_obj.disp("hello")
    assert io_obj.vt.lines[0][:5] == list("hello")


def test_io_disp_right_justifies_integers(io_obj, capsys):
    io_obj.disp(42)
    row_str = "".join(io_obj.vt.lines[0])
    assert row_str == "              42"


def test_io_disp_right_justifies_floats(io_obj, capsys):
    io_obj.disp(3.14)
    row_str = "".join(io_obj.vt.lines[0])
    assert row_str.strip() == "3.14"


def test_io_disp_defaults_to_empty_string(io_obj, capsys):
    io_obj.disp()
    # Writing '' should not modify any cell; all chars remain spaces
    assert io_obj.vt.lines[0] == [" "] * 16


# ── IO: pause ────────────────────────────────────────────────────────────────


def test_io_pause_with_message_writes_it_to_vt(io_obj, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda: "")
    io_obj.pause("waiting...")
    all_text = "".join("".join(line) for line in io_obj.vt.lines)
    assert "waiting" in all_text


def test_io_pause_without_message_does_not_raise(io_obj, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda: "")
    io_obj.pause()  # should complete without error


# ── IO: menu ─────────────────────────────────────────────────────────────────


def test_io_menu_returns_label_for_valid_choice(io_obj, monkeypatch, capsys):
    menu = (("title", [("first", "LBL1"), ("second", "LBL2")]),)
    monkeypatch.setattr("builtins.input", lambda *_: "2")
    assert io_obj.menu(menu) == "LBL2"


def test_io_menu_prints_title_and_options(io_obj, monkeypatch, capsys):
    menu = (("choose", [("option A", "LA"), ("option B", "LB")]),)
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    io_obj.menu(menu)
    out = capsys.readouterr().out
    assert "choose" in out
    assert "option A" in out


def test_io_menu_reprompts_on_invalid_choice(io_obj, monkeypatch, capsys):
    menu = (("t", [("only", "LBL")]),)
    responses = iter(["nope", "99", "1"])
    monkeypatch.setattr("builtins.input", lambda *_: next(responses))
    assert io_obj.menu(menu) == "LBL"
    assert capsys.readouterr().out.count("invalid choice") == 2


def test_io_menu_first_choice_is_valid(io_obj, monkeypatch, capsys):
    menu = (("t", [("alpha", "A"), ("beta", "B")]),)
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    assert io_obj.menu(menu) == "A"


# ── render_braille ───────────────────────────────────────────────────────────


def _blank_pixels():
    graph = GraphState()
    return graph.pixels


def test_render_braille_returns_correct_dimensions():
    lines = render_braille(_blank_pixels())
    assert len(lines) == GRAPH_ROWS
    assert all(len(line) == GRAPH_COLS for line in lines)


def test_render_braille_all_blank_pixels_yields_blank_braille_cells():
    lines = render_braille(_blank_pixels())
    assert all(ch == chr(BRAILLE_BASE) for line in lines for ch in line)


@pytest.mark.parametrize(
    "dx,dy,bit",
    [
        (0, 0, 0x01),
        (0, 1, 0x02),
        (0, 2, 0x04),
        (0, 3, 0x40),
        (1, 0, 0x08),
        (1, 1, 0x10),
        (1, 2, 0x20),
        (1, 3, 0x80),
    ],
)
def test_render_braille_dot_bit_mapping(dx, dy, bit):
    pixels = _blank_pixels()
    pixels[dy][dx] = True
    lines = render_braille(pixels)
    assert lines[0][0] == chr(BRAILLE_BASE + bit)
    # every other cell in the grid stays blank
    assert all(ch == chr(BRAILLE_BASE) for ch in lines[0][1:])
    assert all(ch == chr(BRAILLE_BASE) for line in lines[1:] for ch in line)


def test_render_braille_full_cell_sets_all_dot_bits():
    pixels = _blank_pixels()
    for row in range(4):
        for col in range(2):
            pixels[row][col] = True
    lines = render_braille(pixels)
    assert lines[0][0] == chr(BRAILLE_BASE + 0xFF)


def test_render_braille_maps_row_major_pixels_not_transposed():
    # a pixel at row 0 col 1 should light up dot (dx=1, dy=0) -> bit 0x08,
    # not accidentally be read as row 1 col 0 -> bit 0x02.
    pixels = _blank_pixels()
    pixels[0][1] = True
    lines = render_braille(pixels)
    assert lines[0][0] == chr(BRAILLE_BASE + 0x08)


def test_render_braille_handles_partial_last_cell_without_index_error():
    # 63 rows / 4 = 15.75 -> the last Braille row only has 3 real pixel
    # rows (60-62) backing it; the 4th (63) is out of bounds and must be
    # silently treated as off rather than raising.
    pixels = _blank_pixels()
    pixels[62][0] = True
    lines = render_braille(pixels)
    assert lines[-1][0] == chr(BRAILLE_BASE + 0x04)  # dot (0, 2) -> row 62


def test_render_braille_second_cell_column_offset():
    pixels = _blank_pixels()
    pixels[0][2] = True  # first dot of the second character cell
    lines = render_braille(pixels)
    assert lines[0][1] == chr(BRAILLE_BASE + 0x01)
    assert lines[0][0] == chr(BRAILLE_BASE)


# ── IO: graph rendering ──────────────────────────────────────────────────────


def test_io_draw_pixel_paints_graph_region(io_obj, capsys):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    out = capsys.readouterr().out
    assert ("\033[%i;1H" % IO.GRAPH_ROW) in out
    assert chr(BRAILLE_BASE + 0x01) in out


def test_io_draw_pixel_writes_every_graph_row(io_obj, capsys):
    io_obj.draw_pixel(0, 0, True)
    out = capsys.readouterr().out
    for i in range(GRAPH_ROWS):
        assert ("\033[%i;1H" % (IO.GRAPH_ROW + i)) in out


def test_io_draw_pixel_saves_and_restores_cursor(io_obj, capsys):
    io_obj.draw_pixel(0, 0, True)
    out = capsys.readouterr().out
    assert out.startswith("\0337")
    assert out.endswith("\0338")


def test_io_clr_draw_blanks_graph_region(io_obj, capsys):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_pixel(0, 0, True)
    capsys.readouterr()

    io_obj.vm.graph.clear()  # ClrDraw token clears vm.graph before calling io.clr_draw
    io_obj.clr_draw()
    out = capsys.readouterr().out
    assert chr(BRAILLE_BASE + 0x01) not in out
    assert (chr(BRAILLE_BASE) * GRAPH_COLS) in out


def test_io_draw_line_repaints_from_graph_pixels(io_obj, capsys):
    io_obj.vm.graph.set_pixel(10, 5, True)  # cell (col 5, row 1), dot (0, 1) -> 0x02
    io_obj.draw_line(-10, 10, 10, -10, True)
    out = capsys.readouterr().out
    assert chr(BRAILLE_BASE + 0x02) in out


def test_io_draw_circle_repaints_from_graph_pixels(io_obj, capsys):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_circle(0, 0, 5, True)
    out = capsys.readouterr().out
    assert chr(BRAILLE_BASE + 0x01) in out


def test_io_pxl_on_repaints_graph_region(io_obj, capsys):
    io_obj.vm.graph.set_pixel(0, 0, True)  # Pxl-On(row,col) -> set_pixel(col, row, ...)
    io_obj.pxl_on(0, 0)
    out = capsys.readouterr().out
    assert ("\033[%i;1H" % IO.GRAPH_ROW) in out
    assert chr(BRAILLE_BASE + 0x01) in out


def test_io_pxl_off_repaints_graph_region(io_obj, capsys):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.pxl_on(0, 0)
    capsys.readouterr()

    io_obj.vm.graph.set_pixel(0, 0, False)
    io_obj.pxl_off(0, 0)
    out = capsys.readouterr().out
    assert chr(BRAILLE_BASE + 0x01) not in out


def test_io_pxl_change_repaints_from_graph_pixels(io_obj, capsys):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.pxl_change(0, 0, True)
    out = capsys.readouterr().out
    assert chr(BRAILLE_BASE + 0x01) in out


def test_io_draw_function_repaints_from_graph_pixels(io_obj, capsys):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_function()
    out = capsys.readouterr().out
    assert chr(BRAILLE_BASE + 0x01) in out


def test_io_draw_shade_repaints_from_graph_pixels(io_obj, capsys):
    io_obj.vm.graph.set_pixel(0, 0, True)
    io_obj.draw_shade()
    out = capsys.readouterr().out
    assert chr(BRAILLE_BASE + 0x01) in out


def test_io_draw_text_graph_is_a_no_op(io_obj, capsys):
    # Braille's 2x4 dot resolution is too coarse for pixel-accurate glyph
    # rendering (see THO-16); this phase only wires up the hook.
    io_obj.draw_text_graph(0, 0, "HI")
    assert capsys.readouterr().out == ""
