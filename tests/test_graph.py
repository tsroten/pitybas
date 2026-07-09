import pytest

from conftest import run
from pitybas.graph import GraphState
from pitybas.parse import Parser
from pitybas import tokens


def test_xmin_tokenizes_as_single_token_not_x_then_min():
    code = Parser("Xmin").parse()
    expr = code[0][0]
    assert len(expr.contents) == 1
    assert isinstance(expr.contents[0], tokens.Xmin)


def test_graph_state_defaults_to_ti_standard_window():
    graph = GraphState()
    assert (graph.xmin, graph.xmax, graph.xscl) == (-10, 10, 1)
    assert (graph.ymin, graph.ymax, graph.yscl) == (-10, 10, 1)
    assert graph.axes_on is True


def test_graph_state_pixel_buffer_is_95_by_63():
    graph = GraphState()
    assert len(graph.pixels) == 63
    assert all(len(row) == 95 for row in graph.pixels)
    assert not any(any(row) for row in graph.pixels)


@pytest.mark.parametrize(
    "x,y,px,py",
    [
        (0, 0, 47, 31),
        (-10, 10, 0, 0),
        (10, -10, 94, 62),
        (10, 10, 94, 0),
        (-10, -10, 0, 62),
    ],
)
def test_to_pixel_maps_window_coords_to_pixel_grid(x, y, px, py):
    graph = GraphState()
    assert graph.to_pixel(x, y) == (px, py)


@pytest.mark.parametrize("x,y", [(-10.1, 0), (10.1, 0), (0, -10.1), (0, 10.1)])
def test_to_pixel_returns_none_outside_window(x, y):
    graph = GraphState()
    assert graph.to_pixel(x, y) is None


def test_to_coord_is_inverse_of_to_pixel_at_grid_corners():
    graph = GraphState()
    assert graph.to_coord(0, 0) == (-10, 10)
    assert graph.to_coord(94, 62) == (10, -10)


@pytest.mark.parametrize(
    "xmin,xmax,ymin,ymax",
    [(5, 5, -10, 10), (-10, 10, 5, 5), (5, 5, 5, 5)],
)
def test_to_pixel_returns_none_for_collapsed_window_instead_of_raising(
    xmin, xmax, ymin, ymax
):
    graph = GraphState()
    graph.xmin, graph.xmax = xmin, xmax
    graph.ymin, graph.ymax = ymin, ymax
    assert graph.to_pixel(xmin, ymin) is None


def test_window_variables_default_to_ti_standard():
    vm = run("Disp Xmin\nDisp Xmax\nDisp Ymin\nDisp Ymax\nDisp Xscl\nDisp Yscl")
    assert vm.io.disps == [-10, 10, -10, 10, 1, 1]


def test_window_variables_store_and_read_back():
    vm = run("-5->Xmin\n5->Xmax\n-3->Ymin\n3->Ymax\nDisp Xmin\nDisp Xmax")
    assert vm.io.disps == [-5, 5]
    assert vm.graph.xmin == -5
    assert vm.graph.xmax == 5
    assert vm.graph.ymin == -3
    assert vm.graph.ymax == 3


def test_pt_on_sets_pixel_and_records_draw():
    vm = run("Pt-On(0,0")
    assert vm.graph.get_pixel(47, 31) is True
    assert vm.io.draws == [(47, 31, True)]


def test_pt_off_clears_pixel_and_records_draw():
    vm = run("Pt-On(0,0\nPt-Off(0,0")
    assert vm.graph.get_pixel(47, 31) is False
    assert vm.io.draws == [(47, 31, True), (47, 31, False)]


def test_pt_change_toggles_pixel():
    vm = run("Pt-Change(0,0\nPt-Change(0,0")
    assert vm.graph.get_pixel(47, 31) is False
    assert vm.io.draws == [(47, 31, True), (47, 31, False)]


def test_pt_on_outside_window_is_silently_skipped():
    vm = run("Pt-On(100,100")
    assert vm.io.draws == []
    assert not any(any(row) for row in vm.graph.pixels)


def test_clrdraw_resets_pixel_buffer_and_notifies_io():
    vm = run("Pt-On(0,0\nClrDraw")
    assert not any(any(row) for row in vm.graph.pixels)
    assert vm.io.clr_draws == 1


def test_line_draws_pixels_between_endpoints():
    vm = run("Line(-5,0,5,0")
    assert vm.graph.get_pixel(24, 31) is True
    assert vm.graph.get_pixel(70, 31) is True
    assert vm.graph.get_pixel(47, 31) is True
    assert vm.io.lines == [(-5, 0, 5, 0, True)]
    # shape draws don't also fire the per-pixel Pt-On hook
    assert vm.io.draws == []


def test_line_erase_flag_clears_previously_drawn_pixels():
    vm = run("Line(-5,0,5,0\nLine(-5,0,5,0,0")
    assert not any(any(row) for row in vm.graph.pixels)
    assert vm.io.lines == [(-5, 0, 5, 0, True), (-5, 0, 5, 0, False)]


def test_line_extending_past_window_clips_to_the_visible_segment():
    vm = run("Line(-20,0,20,0")
    assert all(vm.graph.get_pixel(px, 31) for px in range(95))
    # io is notified with the original, unclipped coordinates
    assert vm.io.lines == [(-20, 0, 20, 0, True)]


def test_line_entirely_outside_window_draws_nothing_without_raising():
    vm = run("Line(-20,-20,-15,-15")
    assert not any(any(row) for row in vm.graph.pixels)
    assert vm.io.lines == [(-20, -20, -15, -15, True)]


def test_circle_draws_points_on_the_circumference():
    vm = run("Circle(0,0,5")
    assert vm.graph.get_pixel(70, 31) is True  # (5, 0)
    assert vm.graph.get_pixel(24, 31) is True  # (-5, 0)
    assert vm.graph.get_pixel(47, 16) is True  # (0, 5)
    assert vm.graph.get_pixel(47, 46) is True  # (0, -5)
    assert vm.io.circles == [(0, 0, 5, True)]
    assert vm.io.draws == []


def test_circle_large_radius_outside_window_draws_nothing_without_raising():
    vm = run("Circle(0,0,100")
    assert not any(any(row) for row in vm.graph.pixels)
    assert vm.io.circles == [(0, 0, 100, True)]


def test_circle_samples_enough_points_on_a_tall_skewed_window():
    # Ymax-Ymin is 100x wider than Xmax-Xmin, so a circle spanning the full
    # y-range needs far more samples than an x-only pixel radius would give;
    # under-sampling would leave gaps near the top/bottom of the circle.
    vm = run("-1->Xmin\n1->Xmax\n-50->Ymin\n50->Ymax\nCircle(0,0,40")
    assert vm.graph.get_pixel(47, 6) is True  # (0, 40), the circle's top point
    assert any(any(row) for row in vm.graph.pixels)


def test_circle_with_tiny_window_range_does_not_hang():
    # Xmax-Xmin near zero would make the old x-only step formula explode;
    # steps must be capped to the pixel grid regardless of window scale.
    vm = run("-0.0001->Xmin\n0.0001->Xmax\nCircle(0,0,0.00005")
    assert any(any(row) for row in vm.graph.pixels)


def test_horizontal_draws_a_full_width_row():
    vm = run("Horizontal 0")
    assert all(vm.graph.get_pixel(px, 31) for px in range(95))
    assert vm.io.lines == [(-10, 0, 10, 0, True)]


def test_vertical_draws_a_full_height_column():
    vm = run("Vertical 0")
    assert all(vm.graph.get_pixel(47, py) for py in range(63))
    assert vm.io.lines == [(0, -10, 0, 10, True)]


def test_horizontal_outside_window_draws_nothing_without_raising():
    vm = run("Horizontal 20")
    assert not any(any(row) for row in vm.graph.pixels)
    assert vm.io.lines == [(-10, 20, 10, 20, True)]


def test_pxl_on_sets_pixel_at_row_col_and_records_pxl_hook():
    vm = run("Pxl-On(5,10")
    assert vm.graph.get_pixel(10, 5) is True
    assert vm.io.pxls == [(5, 10, True)]


def test_pxl_on_argument_order_is_row_col_not_x_y():
    # row=5, col=10 must set pixel (col=10, row=5), not (col=5, row=10) --
    # this would fail if Pxl-On mistakenly used Pt-On's x,y order.
    vm = run("Pxl-On(5,10")
    assert vm.graph.get_pixel(10, 5) is True
    assert vm.graph.get_pixel(5, 10) is False


def test_pxl_off_clears_pixel_and_records_pxl_hook():
    vm = run("Pxl-On(5,10\nPxl-Off(5,10")
    assert vm.graph.get_pixel(10, 5) is False
    assert vm.io.pxls == [(5, 10, True), (5, 10, False)]


def test_pxl_change_toggles_pixel():
    vm = run("Pxl-Change(5,10\nPxl-Change(5,10")
    assert vm.graph.get_pixel(10, 5) is False
    assert vm.io.pxls == [(5, 10, True), (5, 10, False)]


def test_pxl_on_outside_grid_is_silently_skipped():
    vm = run("Pxl-On(63,0\nPxl-On(0,95")
    assert vm.io.pxls == []
    assert not any(any(row) for row in vm.graph.pixels)


def test_pxl_on_does_not_fire_the_pt_draw_hook():
    vm = run("Pxl-On(5,10")
    assert vm.io.draws == []


def test_pxl_test_returns_1_when_pixel_is_on():
    vm = run("Pxl-On(5,10\nDisp Pxl-Test(5,10)")
    assert vm.io.disps == [1]


def test_pxl_test_returns_0_when_pixel_is_off():
    vm = run("Disp Pxl-Test(5,10)")
    assert vm.io.disps == [0]


def test_pxl_test_argument_order_is_row_col_not_x_y():
    # only (row=5, col=10) is on; reading back (col=10, row=5) via Pxl-Test's
    # row,col order must see it, while the transposed row,col must not.
    vm = run("Pxl-On(5,10\nDisp Pxl-Test(5,10)\nDisp Pxl-Test(10,5)")
    assert vm.io.disps == [1, 0]


def test_pxl_test_outside_grid_returns_0_without_raising():
    vm = run("Disp Pxl-Test(63,0)\nDisp Pxl-Test(0,95)")
    assert vm.io.disps == [0, 0]


def test_pxl_on_rounds_non_integer_coordinates_instead_of_raising():
    vm = run("Pxl-On(5.5,10.4")
    assert vm.graph.get_pixel(10, 6) is True
    assert vm.io.pxls == [(6, 10, True)]


def test_pxl_test_rounds_non_integer_coordinates_instead_of_raising():
    vm = run("Pxl-On(5.5,10.4\nDisp Pxl-Test(5.5,10.4)")
    assert vm.io.disps == [1]


def test_drawf_plots_the_function_across_the_window():
    vm = run("DrawF X")
    assert vm.graph.get_pixel(0, 62) is True  # (-10, -10)
    assert vm.graph.get_pixel(47, 31) is True  # (0, 0)
    assert vm.graph.get_pixel(94, 0) is True  # (10, 10)


def test_drawf_notifies_io_draw_function_hook():
    vm = run("DrawF X")
    assert vm.io.draw_fs == 1


def test_drawf_restores_the_value_x_held_before_the_call():
    vm = run("5->X\nDrawF X^2\nDisp X")
    assert vm.io.disps == [5]


def test_drawf_leaves_x_undefined_if_it_was_undefined_before_the_call():
    vm = run("DrawF X")
    assert "X" not in vm.vars


def test_axes_off_then_on_toggles_graph_state():
    vm = run("AxesOff")
    assert vm.graph.axes_on is False

    vm = run("AxesOff\nAxesOn")
    assert vm.graph.axes_on is True


def test_zstandard_resets_window_to_ti_standard():
    vm = run("-5->Xmin\n5->Xmax\nZStandard")
    assert (vm.graph.xmin, vm.graph.xmax, vm.graph.xscl) == (-10, 10, 1)
    assert (vm.graph.ymin, vm.graph.ymax, vm.graph.yscl) == (-10, 10, 1)


def test_zdecimal_sets_window_for_tenth_unit_pixel_spacing():
    vm = run("ZDecimal")
    assert (vm.graph.xmin, vm.graph.xmax, vm.graph.xscl) == (-4.7, 4.7, 1)
    assert (vm.graph.ymin, vm.graph.ymax, vm.graph.yscl) == (-3.1, 3.1, 1)
    # the real TI-83/84 ZDecimal window produces exactly 0.1 units/pixel
    # across the 95x63 (94/62 max-index) pixel grid
    assert (vm.graph.xmax - vm.graph.xmin) / 94 == pytest.approx(0.1)
    assert (vm.graph.ymax - vm.graph.ymin) / 62 == pytest.approx(0.1)
