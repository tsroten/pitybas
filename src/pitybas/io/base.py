"""Abstract base class for pitybas IO backends."""

from abc import ABC, abstractmethod


class IOBase(ABC):
    """Abstract base class that all IO backends must implement.

    An IO backend is responsible for rendering output (disp, output, clear)
    and collecting input (input, getkey, pause, menu) on behalf of the
    interpreter.  Subclasses must implement every abstract method.
    """

    def __init__(self, vm):
        self.vm = vm

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @abstractmethod
    def clear(self):
        """Clear the display."""

    @abstractmethod
    def input(self, msg, is_str=False):
        """Prompt the user for input and return the parsed value.

        Args:
            msg: Prompt string shown to the user before reading.
            is_str: When True, return the raw string without parsing.

        Returns:
            The parsed numeric/expression value, or the raw string when
            ``is_str`` is True.
        """

    @abstractmethod
    def getkey(self):
        """Return the keycode of the key currently pressed, or 0."""

    @abstractmethod
    def output(self, row, col, msg):
        """Write *msg* at the given *row* and *col* on the display."""

    @abstractmethod
    def disp(self, msg=""):
        """Display *msg* as a line of output."""

    @abstractmethod
    def pause(self, msg=""):
        """Optionally display *msg*, then wait for the user to press Enter."""

    @abstractmethod
    def menu(self, menu):
        """Display an interactive menu and return the chosen label.

        Args:
            menu: A tuple of ``(title, [(desc, label)])`` entries where
                *title* and *desc* are already-evaluated display strings
                and *label* is a raw token for ``Goto`` to resolve.

        Returns:
            The label string corresponding to the user's selection.
        """
