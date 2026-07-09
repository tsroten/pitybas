"""Scripted IO backend for driving programs in tests."""

import copy

from pitybas.io.base import IOBase
from pitybas.parse import Parser


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

    def __init__(self, vm, inputs=None, keys=None):
        self.vm = vm
        self.inputs = list(inputs or [])
        self.keys = list(keys or [])
        self.disps = []
        self.outputs = []
        self.clears = 0
        self.draws = []
        self.clr_draws = 0
        self.lines = []
        self.circles = []
        self.pxls = []
        self.draw_fs = 0

    def clear(self):
        self.clears += 1

    def input(self, msg, is_str=False):
        val = self.inputs.pop(0)
        if not is_str and isinstance(val, str):
            val = Parser.parse_line(self.vm, val)
        return val

    def getkey(self):
        """Return the next key from *keys*, or ``0`` when the list is empty."""
        if self.keys:
            return self.keys.pop(0)
        return 0

    def output(self, row, col, msg):
        """Record a positioned write as a ``(row, col, msg)`` tuple."""
        self.outputs.append((row, col, msg))

    def disp(self, msg=""):
        # lists/matrices are mutable and stored by reference in the vm;
        # snapshot them so later mutations don't retroactively change
        # already-recorded output.
        self.disps.append(copy.deepcopy(msg))

    def pause(self, msg=""):
        if msg:
            self.disp(msg)

    def menu(self, menu):
        """Select a menu option by 1-based index drawn from *inputs*.

        The next value popped from :attr:`inputs` is treated as a 1-based
        integer index into the flat list of all menu options (across all
        groups), and the corresponding raw label token is returned.
        """
        choice = self.inputs.pop(0)
        lookup = [label for _, entries in menu for _, label in entries]
        return lookup[int(choice) - 1]

    def draw_pixel(self, px, py, on):
        """Record a graph-screen pixel change as a ``(px, py, on)`` tuple."""
        self.draws.append((px, py, on))

    def clr_draw(self):
        """Record a graph-screen clear."""
        self.clr_draws += 1

    def draw_line(self, x1, y1, x2, y2, on):
        """Record a Line(/Horizontal/Vertical draw as a tuple."""
        self.lines.append((x1, y1, x2, y2, on))

    def draw_circle(self, x, y, r, on):
        """Record a Circle( draw as a tuple."""
        self.circles.append((x, y, r, on))

    def pxl_on(self, row, col):
        """Record a Pxl-On( as a ``(row, col, True)`` tuple."""
        self.pxls.append((row, col, True))

    def pxl_off(self, row, col):
        """Record a Pxl-Off( as a ``(row, col, False)`` tuple."""
        self.pxls.append((row, col, False))

    def pxl_change(self, row, col, on):
        """Record a Pxl-Change( as a ``(row, col, on)`` tuple."""
        self.pxls.append((row, col, on))

    def draw_function(self):
        """Record a DrawF plot."""
        self.draw_fs += 1
