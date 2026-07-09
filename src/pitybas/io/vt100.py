try:
    import readline  # noqa: F401 - imported for side effects (enables input history in the REPL)
except ImportError:
    pass

from pitybas.parse import Parser
from pitybas.common import ParseError
from pitybas.io.base import IOBase

import select
import sys
import termios
import time
import tty

keycodes = {
    "left": 24,
    "up": 25,
    "right": 26,
    "down": 34,
    "A": 41,
    "B": 42,
    "C": 43,
    "D": 51,
    "E": 52,
    "F": 53,
    "G": 54,
    "H": 55,
    "I": 61,
    "J": 62,
    "K": 63,
    "L": 64,
    "M": 65,
    "N": 71,
    "O": 72,
    "P": 73,
    "Q": 74,
    "R": 75,
    "S": 81,
    "T": 82,
    "U": 83,
    "V": 84,
    "W": 85,
    "X": 91,
    "Y": 92,
    "Z": 93,
    '"': 95,
    " ": 102,
    ":": 103,
    "?": 104,
    "enter": 105,
}


# Graph-screen Braille rendering ─────────────────────────────────────────────
#
# vm.graph.pixels (see pitybas.graph.GraphState) is a 63-row x 95-col
# buffer, row-major: pixels[row][col]. Packing a 2 (wide) x 4 (tall) block
# of dots into each Unicode Braille character (U+2800+) gives a 48x16
# character grid, small enough to sit below the 16x8 text screen inside a
# normal terminal window.
#
# Braille dot layout is not raster order: dots 1-2-3 run down the left
# column with dot 7 at the bottom-left, dots 4-5-6 run down the right
# column with dot 8 at the bottom-right. (dx, dy, bit) below maps a pixel's
# offset within its 2x4 cell to the bit it contributes to the character.
BRAILLE_BASE = 0x2800
BRAILLE_DOTS = (
    (0, 0, 0x01),
    (0, 1, 0x02),
    (0, 2, 0x04),
    (0, 3, 0x40),
    (1, 0, 0x08),
    (1, 1, 0x10),
    (1, 2, 0x20),
    (1, 3, 0x80),
)

GRAPH_COLS = 48  # ceil(PIXEL_COLS / 2)
GRAPH_ROWS = 16  # ceil(PIXEL_ROWS / 4)


def render_braille(pixels):
    """Render a row-major pixel buffer as Braille text.

    Args:
        pixels: Row-major pixel buffer (``pixels[row][col]``), truthy for
            an "on" pixel, as found on ``GraphState.pixels``.

    Returns:
        A list of ``GRAPH_ROWS`` strings, each ``GRAPH_COLS`` Braille
        characters wide, packing a 2 (wide) x 4 (tall) block of pixels into
        each character.
    """
    rows = len(pixels)
    cols = len(pixels[0]) if rows else 0

    lines = []
    for cell_row in range(GRAPH_ROWS):
        chars = []
        for cell_col in range(GRAPH_COLS):
            bits = 0
            for dx, dy, bit in BRAILLE_DOTS:
                px, py = cell_col * 2 + dx, cell_row * 4 + dy
                if px < cols and py < rows and pixels[py][px]:
                    bits |= bit
            chars.append(chr(BRAILLE_BASE + bits))
        lines.append("".join(chars))
    return lines


class Delayed:
    """
    ensure at least duration time between __enter__ and __exit__
    """

    def __init__(self, duration):
        self.duration = duration

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        diff = self.duration - (time.time() - self.start)
        if diff > 0:
            time.sleep(diff)


class SafeIO:
    def __init__(self, fd):
        self.fd = fd

    def __enter__(self):
        self.old = termios.tcgetattr(self.fd)

    def __exit__(self, *args):
        termios.tcsetattr(self.fd, termios.TCSANOW, self.old)


class VT:
    def __init__(self, width=16, height=8):
        self.width = width
        self.height = height
        self.clear()

        self.row, self.col = 1, 1
        self.pos_stack = []

    def push(self):
        self.pos_stack.append((self.row, self.col))

    def pop(self):
        self.row, self.col = self.pos_stack.pop()

    def e(self, *seqs):
        for seq in seqs:
            sys.stdout.write("\033" + seq)

    def clear(self, reset=True):
        self.e("[2J", "[H")
        self.row, self.col = 1, 1
        if reset:
            self.lines = []
            for i in range(self.height):
                self.lines.append([" "] * self.width)

    def scroll(self):
        self.lines.pop(0)
        self.lines.append([" "] * self.width)
        self.row = max(1, self.row - 1)

    def flush(self):
        self.clear(reset=False)
        data = "\n".join("".join(line) for line in self.lines) + "\n"
        sys.stdout.write(data)

    def move(self, row, col):
        self.row, self.col = row, col
        self.e("[%i;%iH" % (row, col))

    def wrap(self, msg):
        msg = str(msg)
        first = self.width - self.col + 1
        first, msg = msg[:first], msg[first:]
        lines = [first]
        while msg:
            lines.append(msg[: self.width])
            msg = msg[self.width :]

        return lines

    def write(self, msg, scroll=True):
        row, col = self.row, self.col
        self.e("[%i;%iH" % (row, col))

        for line in self.wrap(msg):
            if row > self.height:
                row -= 1

                if scroll:
                    self.scroll()
                    row, col = self.row, self.col
                    self.flush()
                    self.move(row, 1)
                else:
                    break

            for char in line:
                self.lines[row - 1][col - 1] = char
                sys.stdout.write(char)
                col += 1

            col = 1
            row += 1
            sys.stdout.write("\n")

        self.row, self.col = row, col

    def output(self, row, col, msg):
        self.e("7")
        old = self.row, self.col
        self.move(row, col)
        self.write(msg)

        self.row, self.col = old
        self.e("8")

    def getch(self):
        fd = sys.stdin.fileno()

        with SafeIO(fd):
            tty.setraw(fd)

            with Delayed(0.1):
                ins, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not ins:
                return

            ch = sys.stdin.read(1)
            if ch == "\003":
                raise KeyboardInterrupt

            if ch in ("\r", "\n"):
                return "enter"

            if ch == "\033":
                # control sequence
                ch = sys.stdin.read(1)
                if ch == "[":
                    ch = sys.stdin.read(1)
                    if ch == "A":
                        return "up"
                    elif ch == "B":
                        return "down"
                    elif ch == "C":
                        return "right"
                    elif ch == "D":
                        return "left"

                return None

            return ch


class IO(IOBase):
    # Fixed screen layout: the 16x8 text screen (VT, above) occupies
    # terminal rows 1-8, row 9 is reserved for Input/Prompt's prompt line
    # (see input() below, which moves to row 9), and the 48x16 Braille
    # graph region starts at row 10, so none of the three ever overlap.
    GRAPH_ROW = 10
    GRAPH_COL = 1

    def __init__(self, vm):
        self.vm = vm
        self.vt = VT()

    def __enter__(self):
        self.vt.e("[?25l")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Mirror a real TI-83/84: the last screen a program drew (here, the
        # graph) stays up until the user dismisses it, rather than the
        # process exiting straight back to the shell out from under it.
        # Skip the wait on an unhandled exception so the traceback (printed
        # by cli.py after this exits) isn't gated behind a keypress, and
        # skip it if the graph is currently blank (nothing to protect).
        if exc_type is None and any(any(row) for row in self.vm.graph.pixels):
            while self.vt.getch() is None:
                pass

        self.vt.e("[?25h")

    def clear(self):
        self.vt.clear()

    def input(self, msg, is_str=False):
        # TODO: implement this in VT terms
        while True:
            try:
                self.vt.push()
                self.vt.move(9, 1)

                if msg:
                    print(msg, end=" ")

                self.vt.e("[?25h")
                line = input()
                self.vt.e("[?25l")

                self.vt.flush()
                self.vt.pop()
                if not is_str:
                    val = Parser.parse_line(self.vm, line)
                else:
                    val = line

                return val
            except ParseError:
                print("ERR:DATA")
                print()

    def getkey(self):
        key = self.vt.getch()
        if key in keycodes:
            return keycodes[key]
        else:
            return 0

    def output(self, row, col, msg):
        self.vt.output(row, col, msg)
        self.vt.flush()

    def disp(self, msg=""):
        if isinstance(msg, (complex, int, float)):
            msg = str(msg).rjust(16)

        self.vt.write(msg)

    def pause(self, msg=""):
        if msg:
            self.disp(msg)
        self.input("[press enter]", True)

    def menu(self, menu):
        # menu is a tuple of (title, [(desc, label)]) -- title/desc are
        # already-evaluated display strings; label is a raw, unevaluated
        # token for Goto to resolve.
        # TODO: implement this in VT terms

        while True:
            lookup = []
            self.vt.clear(reset=False)
            i = 1

            for title, entries in menu:
                print("-[ %s ]-" % title)
                for name, label in entries:
                    print("%i: %s" % (i, name))
                    lookup.append(label)
                    i += 1

            self.vt.e("[?25h")
            choice = input("choice? ")
            self.vt.e("[?25l")
            print()
            if choice.isdigit() and 0 < int(choice) <= len(lookup):
                label = lookup[int(choice) - 1]
                self.vt.flush()
                return label
            else:
                print("invalid choice")

    def _paint_graph(self):
        """Repaint the whole Braille graph region from vm.graph.pixels.

        draw_line/draw_circle mutate vm.graph.pixels directly (see
        tokens._plot_line and the circle point-generation loop) and only
        notify the IO backend with the original, unclipped window
        coordinates -- not per-pixel updates -- so the shape can't be
        reconstructed from those args alone. Repainting the full grid on
        every callback is cheap at 48x16 characters.
        """
        self.vt.e("7")
        for i, line in enumerate(render_braille(self.vm.graph.pixels)):
            self.vt.e("[%i;%iH" % (self.GRAPH_ROW + i, self.GRAPH_COL))
            sys.stdout.write(line)
        self.vt.e("8")
        sys.stdout.flush()

    def draw_pixel(self, px, py, on):
        self._paint_graph()

    def clr_draw(self):
        self._paint_graph()

    def draw_line(self, x1, y1, x2, y2, on):
        self._paint_graph()

    def draw_circle(self, x, y, r, on):
        self._paint_graph()

    def pxl_on(self, row, col):
        self._paint_graph()

    def pxl_off(self, row, col):
        self._paint_graph()

    def pxl_change(self, row, col, on):
        self._paint_graph()
