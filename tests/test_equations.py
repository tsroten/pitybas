import pytest

from conftest import run
from pitybas.common import ExecutionError
from pitybas.parse import Parser
from pitybas import tokens


def lit_count(vm):
    """Total number of lit pixels in the graph buffer."""
    return sum(sum(row) for row in vm.graph.pixels)


# -- tokenizing ------------------------------------------------------------


@pytest.mark.parametrize(
    "slot", ["Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9", "Y0"]
)
def test_yslot_tokenizes_as_single_variable_not_y_then_digit(slot):
    code = Parser(slot).parse()
    expr = code[0][0]
    assert len(expr.contents) == 1
    token = expr.contents[0]
    assert isinstance(token, tokens.EquationVar)
    assert token.slot == slot


@pytest.mark.parametrize("slot", ["Y1", "Y9", "Y0"])
def test_yslot_supports_function_call_form(slot):
    code = Parser("%s(5)" % slot).parse()
    token = code[0][0].contents[0]
    assert isinstance(token, tokens.EquationFunc)
    assert token.slot == slot


def test_yslots_are_distinct_tokens():
    y1 = Parser("Y1").parse()[0][0].contents[0]
    y2 = Parser("Y2").parse()[0][0].contents[0]
    assert type(y1) is not type(y2)
    assert y1.slot != y2.slot


def test_bare_y_letter_still_tokenizes_as_numvar():
    # a plain "Y" (no digit) must remain the ordinary letter variable
    token = Parser("Y").parse()[0][0].contents[0]
    assert isinstance(token, tokens.NumVar)
    assert not isinstance(token, tokens.EquationVar)


# -- storage / reading -----------------------------------------------------


def test_store_string_holds_expression_unevaluated():
    vm = run('"X²→Y1')
    eq = vm.graph.equations["Y1"]
    assert eq["enabled"] is True
    # stored unevaluated -- re-read gives the value for the current X
    assert eq["expr"] is not None


def test_store_uses_optional_closing_quote_form():
    vm = run('"X²"→Y1\n3->X\nDisp Y1')
    assert vm.io.disps == [9]


@pytest.mark.parametrize("slot", ["Y1", "Y5", "Y9", "Y0"])
def test_store_and_read_each_slot(slot):
    vm = run('"X²→%s\n4->X\nDisp %s' % (slot, slot))
    assert vm.io.disps == [16]


def test_storing_non_string_raises_data_type():
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        run("5→Y1")


def test_storing_expression_result_raises_data_type():
    with pytest.raises(ExecutionError, match="ERR:DATA TYPE"):
        run("2+3→Y1")


def test_bare_read_evaluates_at_current_x():
    vm = run('"X²→Y1\n5->X\nDisp Y1')
    assert vm.io.disps == [25]


def test_reading_undefined_slot_raises_undefined():
    with pytest.raises(ExecutionError, match="ERR:UNDEFINED"):
        run("Disp Y4")


def test_bare_read_does_not_disturb_x():
    vm = run('"X²→Y1\n5->X\nDisp Y1\nDisp X')
    assert vm.io.disps == [25, 5]


# -- callable form ---------------------------------------------------------


def test_call_form_binds_x_to_argument():
    vm = run('"X²→Y1\nDisp Y1(3)')
    assert vm.io.disps == [9]


def test_call_form_restores_x_afterward():
    vm = run('"X²→Y1\n7->X\nDisp Y1(3)\nDisp X')
    assert vm.io.disps == [9, 7]


def test_call_form_leaves_x_undefined_if_it_was_undefined():
    vm = run('"X²→Y1\nDisp Y1(3)')
    assert "X" not in vm.vars


def test_cross_reference_between_slots():
    # Y2 defined as -Y1; reading Y2 evaluates Y1 at the current X
    vm = run('"X→Y1\n"-Y1→Y2\n4->X\nDisp Y2')
    assert vm.io.disps == [-4]


def test_combination_of_slots():
    vm = run('"X→Y1\n"2X→Y2\n"Y1+Y2→Y3\n5->X\nDisp Y3')
    assert vm.io.disps == [15]


def test_composition_via_call_form():
    # Y3 = Y1(Y2): evaluate Y2 at current X, then Y1 with X bound to that
    vm = run('"2X→Y1\n"X+1→Y2\n"Y1(Y2)→Y3\n3->X\nDisp Y3')
    assert vm.io.disps == [8]  # 2 * (3 + 1)


# -- enabled / disabled flag ----------------------------------------------


def test_defining_slot_defaults_to_enabled():
    vm = run('"X→Y1')
    assert vm.graph.equations["Y1"]["enabled"] is True


def test_fnoff_disables_and_fnon_reenables():
    vm = run('"X→Y1\nFnOff 1')
    assert vm.graph.equations["Y1"]["enabled"] is False

    vm = run('"X→Y1\nFnOff 1\nFnOn 1')
    assert vm.graph.equations["Y1"]["enabled"] is True


def test_fnoff_without_argument_disables_all():
    vm = run('"X→Y1\n"X→Y2\nFnOff')
    assert vm.graph.equations["Y1"]["enabled"] is False
    assert vm.graph.equations["Y2"]["enabled"] is False


def test_redefining_a_disabled_slot_reselects_it():
    vm = run('"X→Y1\nFnOff 1\n"2X→Y1')
    assert vm.graph.equations["Y1"]["enabled"] is True


def test_disabled_slot_still_evaluable_directly():
    vm = run('"X²→Y1\nFnOff 1\n4->X\nDisp Y1')
    assert vm.io.disps == [16]


def test_disabled_slot_still_referenceable_from_another_slot():
    vm = run('"X→Y1\nFnOff 1\n"Y1+1→Y2\n4->X\nDisp Y2')
    assert vm.io.disps == [5]


# -- DispGraph -------------------------------------------------------------


def test_dispgraph_plots_enabled_slot():
    vm = run('"X→Y1\nDispGraph')
    assert vm.graph.get_pixel(0, 62) is True  # (-10, -10)
    assert vm.graph.get_pixel(47, 31) is True  # (0, 0)
    assert vm.graph.get_pixel(94, 0) is True  # (10, 10)


def test_dispgraph_notifies_io_draw_function_hook():
    vm = run('"X→Y1\nDispGraph')
    assert vm.io.draw_fs == 1


def test_dispgraph_skips_disabled_slots():
    vm = run('"X→Y1\nFnOff 1\nDispGraph')
    assert lit_count(vm) == 0


def test_dispgraph_is_a_noop_for_undefined_slots():
    vm = run("DispGraph")
    assert lit_count(vm) == 0


def test_dispgraph_restores_x():
    vm = run('5->X\n"X²→Y1\nDispGraph\nDisp X')
    assert vm.io.disps == [5]


def test_dispgraph_leaves_x_undefined_if_it_was_undefined():
    vm = run('"X→Y1\nDispGraph')
    assert "X" not in vm.vars


def test_dispgraph_plots_multiple_enabled_slots():
    vm = run('"X→Y1\n"0X→Y2\nDispGraph')
    assert vm.graph.get_pixel(94, 0) is True  # Y1 at (10, 10)
    assert vm.graph.get_pixel(0, 31) is True  # Y2=0 along the x-axis


# -- Xres ------------------------------------------------------------------


def test_xres_defaults_to_one():
    vm = run("Disp Xres")
    assert vm.io.disps == [1]
    assert vm.graph.xres == 1


def test_xres_tokenizes_as_single_token():
    token = Parser("Xres").parse()[0][0].contents[0]
    assert isinstance(token, tokens.Xres)


def test_xres_stores_and_reads_back():
    vm = run("6→Xres\nDisp Xres")
    assert vm.io.disps == [6]
    assert vm.graph.xres == 6


@pytest.mark.parametrize("value", ["0", "9", "1.5"])
def test_xres_rejects_out_of_range_values(value):
    with pytest.raises(ExecutionError, match="ERR:DOMAIN"):
        run("%s→Xres" % value)


def test_xres_changes_dispgraph_sample_count():
    fine = run('"X→Y1\nDispGraph')
    coarse = run('8→Xres\n"X→Y1\nDispGraph')
    assert lit_count(coarse) < lit_count(fine)


def test_xres_does_not_change_drawf_sample_count():
    fine = run("DrawF X")
    coarse = run("8→Xres\nDrawF X")
    assert lit_count(coarse) == lit_count(fine)


# -- DrawInv ---------------------------------------------------------------


def test_drawinv_swaps_axes_relative_to_drawf():
    # DrawInv 0 plots (0, X) for every X -> a vertical line at x=0 (col 47),
    # exactly the reflection of DrawF 0's horizontal line at y=0 (row 31).
    vm = run("DrawInv 0")
    assert all(vm.graph.get_pixel(47, py) for py in range(63))
    assert not all(vm.graph.get_pixel(px, 31) for px in range(95))


def test_drawinv_of_identity_is_the_diagonal():
    vm = run("DrawInv X")
    assert vm.graph.get_pixel(0, 62) is True
    assert vm.graph.get_pixel(47, 31) is True
    assert vm.graph.get_pixel(94, 0) is True


def test_drawinv_notifies_io_draw_function_hook():
    vm = run("DrawInv X")
    assert vm.io.draw_fs == 1


def test_drawinv_restores_x():
    vm = run("5->X\nDrawInv X²\nDisp X")
    assert vm.io.disps == [5]


def test_drawinv_ignores_xres():
    fine = run("DrawInv X")
    coarse = run("8→Xres\nDrawInv X")
    assert lit_count(coarse) == lit_count(fine)


# -- GDB integration -------------------------------------------------------


def test_storegdb_recallgdb_round_trips_equations_and_flags():
    vm = run(
        '"X→Y1\n"2X→Y2\nFnOff 2\nStoreGDB 1\n'
        '"99→Y1\nFnOn 2\nRecallGDB 1\n'
        "5->X\nDisp Y1\nDisp Y2"
    )
    # definitions restored: Y1 back to X (5), Y2 to 2X (10)
    assert vm.io.disps == [5, 10]
    # selection flags restored: Y1 enabled, Y2 disabled
    assert vm.graph.equations["Y1"]["enabled"] is True
    assert vm.graph.equations["Y2"]["enabled"] is False


def test_recallgdb_fully_replaces_all_slots():
    # Y3 is defined *after* the GDB was stored; recalling must clear it,
    # matching real hardware's full-replace (not merge) semantics.
    vm = run('"X→Y1\nStoreGDB 1\n"99→Y3\nRecallGDB 1')
    assert "Y1" in vm.graph.equations
    assert "Y3" not in vm.graph.equations


def test_recallgdb_recalls_a_slot_blank_at_store_time_as_blank():
    vm = run('StoreGDB 1\n"X→Y1\nRecallGDB 1')
    assert vm.graph.equations == {}


def test_xres_round_trips_through_gdb():
    vm = run("7→Xres\nStoreGDB 2\n1→Xres\nRecallGDB 2\nDisp Xres")
    assert vm.io.disps == [7]


def test_recallgdb_snapshot_is_independent_of_later_redefinition():
    # redefining a slot after StoreGDB must not mutate the stored snapshot
    vm = run('"X→Y1\nStoreGDB 1\n"2X→Y1\nRecallGDB 1\n5->X\nDisp Y1')
    assert vm.io.disps == [5]
