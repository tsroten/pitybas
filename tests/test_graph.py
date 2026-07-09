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
