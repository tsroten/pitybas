try:
    import readline  # noqa: F401 - imported for side effects (enables input history in the REPL)
except ImportError:
    pass

from typing import Any

from pitybas.parse import Parser
from pitybas.common import ParseError
from pitybas.io.base import IOBase


class IO(IOBase):
    def clear(self) -> None:
        print("-" * 16)

    def input(self, msg: str, is_str: bool = False) -> Any:
        while True:
            try:
                if msg:
                    print(msg, end=" ")

                line = input()
                if not is_str:
                    val = Parser.parse_line(self.vm, line)
                else:
                    val = line

                return val
            except ParseError:
                print("ERR:DATA")
                print()

    def getkey(self) -> int:
        raise NotImplementedError

    def output(self, x: int, y: int, msg: object) -> None:
        print(msg)

    def disp(self, msg: object = "") -> None:
        print(msg)

    def pause(self, msg: object = "") -> None:
        if msg:
            self.disp(msg)
        self.input("[press enter]", True)

    def menu(self, menu: Any) -> Any:
        # menu is a tuple of (title, [(desc, label)]) -- title/desc are
        # already-evaluated display strings; label is a raw, unevaluated
        # token for Goto to resolve.
        while True:
            lookup = []
            i = 1

            for title, entries in menu:
                print("-[ %s ]-" % title)
                for name, label in entries:
                    print("%i: %s" % (i, name))
                    lookup.append(label)
                    i += 1

            choice = self.input("choice?", True)
            print()
            if choice.isdigit() and 0 < int(choice) <= len(lookup):
                label = lookup[int(choice) - 1]
                return label
            else:
                print("invalid choice")

    def draw_pixel(self, px: int, py: int, on: bool) -> None:
        pass

    def clr_draw(self) -> None:
        pass

    def draw_line(self, x1: float, y1: float, x2: float, y2: float, on: bool) -> None:
        pass

    def draw_circle(self, x: float, y: float, r: float, on: bool) -> None:
        pass

    def pxl_on(self, row: int, col: int) -> None:
        pass

    def pxl_off(self, row: int, col: int) -> None:
        pass

    def pxl_change(self, row: int, col: int, on: bool) -> None:
        pass

    def draw_function(self) -> None:
        pass

    def draw_shade(self) -> None:
        pass

    def draw_text_graph(self, row: int, col: int, msg: str) -> None:
        pass
