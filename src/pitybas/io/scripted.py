"""Scripted IO backend for driving programs in tests."""

import copy
from typing import Any, List, Optional, Tuple, TYPE_CHECKING

from pitybas.io.base import IOBase
from pitybas.parse import Parser

if TYPE_CHECKING:
    from pitybas.interpret import Interpreter


class ScriptedIO(IOBase):
    """An IO backend that serves canned inputs and records all output.

    Designed for use in tests: pre-supply a list of *inputs* (consumed by
    ``Input``, ``Prompt``, and ``Menu`` instructions in program order) and an
    optional list of *keys* (consumed by ``getKey`` calls, falling back to
    ``0`` — no key held — once exhausted).  All output is recorded so tests
    can assert on it without touching ``stdin``/``stdout``.

    Attributes:
        disps: List of values passed to :meth:`disp`, in order.
        outputs: List of ``(row, col, msg)`` tuples passed to :meth:`output`.
        clears: Number of times :meth:`clear` was called.
        draws: List of ``(px, py, on)`` tuples passed to :meth:`draw_pixel`.
        clr_draws: Number of times :meth:`clr_draw` was called.
        lines: List of ``(x1, y1, x2, y2, on)`` tuples passed to
            :meth:`draw_line`.
        circles: List of ``(x, y, r, on)`` tuples passed to
            :meth:`draw_circle`.
        pxls: List of ``(row, col, on)`` tuples passed to :meth:`pxl_on`,
            :meth:`pxl_off`, and :meth:`pxl_change`.
        draw_fs: Number of times :meth:`draw_function` was called.
        shades: Number of times :meth:`draw_shade` was called.
        texts: List of ``(row, col, msg)`` tuples passed to
            :meth:`draw_text_graph`.

    Example::

        from pitybas.interpret import Interpreter
        from pitybas.io.scripted import ScriptedIO

        vm = Interpreter.from_string(
            'Input A\\nDisp A*2',
            io=lambda vm: ScriptedIO(vm, inputs=['21']),
        )
        vm.execute()
        assert vm.io.disps == [42]
    """

    def __init__(
        self,
        vm: "Interpreter",
        inputs: Optional[List[Any]] = None,
        keys: Optional[List[int]] = None,
    ) -> None:
        self.vm = vm
        self.inputs: List[Any] = list(inputs or [])
        self.keys: List[int] = list(keys or [])
        self.disps: List[Any] = []
        self.outputs: List[Tuple[int, int, Any]] = []
        self.clears = 0
        self.draws: List[Tuple[int, int, bool]] = []
        self.clr_draws = 0
        self.lines: List[Tuple[float, float, float, float, bool]] = []
        self.circles: List[Tuple[float, float, float, bool]] = []
        self.pxls: List[Tuple[int, int, bool]] = []
        self.draw_fs = 0
        self.shades = 0
        self.texts: List[Tuple[int, int, str]] = []

    def clear(self) -> None:
        self.clears += 1

    def input(self, msg: str, is_str: bool = False) -> Any:
        val = self.inputs.pop(0)
        if not is_str and isinstance(val, str):
            val = Parser.parse_line(self.vm, val)
        return val

    def getkey(self) -> int:
        """Return the next key from *keys*, or ``0`` when the list is empty."""
        if self.keys:
            return self.keys.pop(0)
        return 0

    def output(self, row: int, col: int, msg: object) -> None:
        """Record a positioned write as a ``(row, col, msg)`` tuple."""
        self.outputs.append((row, col, msg))

    def disp(self, msg: object = "") -> None:
        # lists/matrices are mutable and stored by reference in the vm;
        # snapshot them so later mutations don't retroactively change
        # already-recorded output.
        self.disps.append(copy.deepcopy(msg))

    def pause(self, msg: object = "") -> None:
        if msg:
            self.disp(msg)

    def menu(self, menu: Any) -> Optional[str]:
        """Select a menu option by 1-based index drawn from *inputs*.

        The next value popped from :attr:`inputs` is treated as a 1-based
        integer index into the flat list of all menu options (across all
        groups), and the corresponding raw label token is returned.
        """
        choice = self.inputs.pop(0)
        lookup = [label for _, entries in menu for _, label in entries]
        return lookup[int(choice) - 1]

    def draw_pixel(self, px: int, py: int, on: bool) -> None:
        """Record a graph-screen pixel change as a ``(px, py, on)`` tuple."""
        self.draws.append((px, py, on))

    def clr_draw(self) -> None:
        """Record a graph-screen clear."""
        self.clr_draws += 1

    def draw_line(self, x1: float, y1: float, x2: float, y2: float, on: bool) -> None:
        """Record a Line(/Horizontal/Vertical draw as a tuple."""
        self.lines.append((x1, y1, x2, y2, on))

    def draw_circle(self, x: float, y: float, r: float, on: bool) -> None:
        """Record a Circle( draw as a tuple."""
        self.circles.append((x, y, r, on))

    def pxl_on(self, row: int, col: int) -> None:
        """Record a Pxl-On( as a ``(row, col, True)`` tuple."""
        self.pxls.append((row, col, True))

    def pxl_off(self, row: int, col: int) -> None:
        """Record a Pxl-Off( as a ``(row, col, False)`` tuple."""
        self.pxls.append((row, col, False))

    def pxl_change(self, row: int, col: int, on: bool) -> None:
        """Record a Pxl-Change( as a ``(row, col, on)`` tuple."""
        self.pxls.append((row, col, on))

    def draw_function(self) -> None:
        """Record a DrawF plot."""
        self.draw_fs += 1

    def draw_shade(self) -> None:
        """Record a Shade( fill."""
        self.shades += 1

    def draw_text_graph(self, row: int, col: int, msg: str) -> None:
        """Record a Text( call as a ``(row, col, msg)`` tuple."""
        self.texts.append((row, col, msg))
