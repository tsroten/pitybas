"""Abstract base class for pitybas IO backends."""

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pitybas.interpret import Interpreter


class IOBase(ABC):
    """Abstract base class that all IO backends must implement.

    An IO backend is responsible for rendering output (disp, output, clear)
    and collecting input (input, getkey, pause, menu) on behalf of the
    interpreter.  Subclasses must implement every abstract method.
    """

    def __init__(self, vm: "Interpreter") -> None:
        self.vm = vm

    def __enter__(self) -> "IOBase":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the display."""

    @abstractmethod
    def input(self, msg: str, is_str: bool = False) -> Any:
        """Prompt the user for input and return the parsed value.

        Args:
            msg: Prompt string shown to the user before reading.
            is_str: When True, return the raw string without parsing.

        Returns:
            The parsed numeric/expression value, or the raw string when
            ``is_str`` is True.
        """

    @abstractmethod
    def getkey(self) -> int:
        """Return the keycode of the key currently pressed, or 0."""

    @abstractmethod
    def output(self, row: int, col: int, msg: object) -> None:
        """Write *msg* at the given *row* and *col* on the display."""

    @abstractmethod
    def disp(self, msg: object = "") -> None:
        """Display *msg* as a line of output."""

    @abstractmethod
    def pause(self, msg: object = "") -> None:
        """Optionally display *msg*, then wait for the user to press Enter."""

    @abstractmethod
    def menu(self, menu: Any) -> Optional[str]:
        """Display an interactive menu and return the chosen label.

        Args:
            menu: A tuple of ``(title, [(desc, label)])`` entries where
                *title* and *desc* are already-evaluated display strings
                and *label* is a raw token for ``Goto`` to resolve.

        Returns:
            The label string corresponding to the user's selection.
        """

    @abstractmethod
    def draw_pixel(self, px: int, py: int, on: bool) -> None:
        """Render a single graph-screen pixel changing state.

        Args:
            px: Pixel column, 0-94.
            py: Pixel row, 0-62.
            on: True if the pixel was turned on, False if turned off.
        """

    @abstractmethod
    def clr_draw(self) -> None:
        """Render the graph screen's drawn points/lines being cleared."""

    @abstractmethod
    def draw_line(self, x1: float, y1: float, x2: float, y2: float, on: bool) -> None:
        """Render a Line(/Horizontal/Vertical draw in window coordinates.

        Args:
            x1, y1, x2, y2: Window-coordinate endpoints of the line, as
                passed to the token (not clipped to the window).
            on: True if the line was drawn, False if erased.
        """

    @abstractmethod
    def draw_circle(self, x: float, y: float, r: float, on: bool) -> None:
        """Render a Circle( draw in window coordinates.

        Args:
            x, y, r: Window-coordinate center and radius, as passed to the
                token (not clipped to the window).
            on: True if the circle was drawn, False if erased.
        """

    @abstractmethod
    def pxl_on(self, row: int, col: int) -> None:
        """Render a Pxl-On( turning the pixel at (row, col) on.

        Args:
            row: Pixel row, 0-62.
            col: Pixel column, 0-94.
        """

    @abstractmethod
    def pxl_off(self, row: int, col: int) -> None:
        """Render a Pxl-Off( turning the pixel at (row, col) off.

        Args:
            row: Pixel row, 0-62.
            col: Pixel column, 0-94.
        """

    @abstractmethod
    def pxl_change(self, row: int, col: int, on: bool) -> None:
        """Render a Pxl-Change( toggling the pixel at (row, col).

        Args:
            row: Pixel row, 0-62.
            col: Pixel column, 0-94.
            on: The pixel's new state after the toggle.
        """

    @abstractmethod
    def draw_function(self) -> None:
        """Render a DrawF plot of the graph screen's pixel buffer."""

    @abstractmethod
    def draw_shade(self) -> None:
        """Render a Shade( fill of the graph screen's pixel buffer."""

    @abstractmethod
    def draw_text_graph(self, row: int, col: int, msg: str) -> None:
        """Render a Text( string at raw pixel (row, col) on the graph screen.

        Args:
            row: Pixel row, 0-57 (tighter than the general 0-62 grid bound
                so a 6px-tall glyph always fits).
            col: Pixel column, 0-94.
            msg: The already-concatenated display string to render.
        """
