"""Graph screen state: window variables, pixel buffer, coordinate mapping.

The addressable graph-pixel grid is 95x63 (columns 0-94, rows 0-62) -- the
real TI-83/84 convention, not the full 96x64 LCD resolution. See
``to_pixel``/``to_coord`` for the coordinate mapping every drawing token
reuses.
"""

PIXEL_COLS = 95
PIXEL_ROWS = 63
MAX_COL = PIXEL_COLS - 1
MAX_ROW = PIXEL_ROWS - 1

# Text( uses the same 95x63 grid as everything else, but a 6px-tall glyph
# needs to fit inside the 63-row grid, so its row bound is tighter than the
# general MAX_ROW.
TEXT_MAX_ROW = PIXEL_ROWS - 6


class GraphState:
    def __init__(self):
        self.xmin = -10
        self.xmax = 10
        self.xscl = 1
        self.ymin = -10
        self.ymax = 10
        self.yscl = 1
        self.axes_on = True

        self.pixels = [[False] * PIXEL_COLS for _ in range(PIXEL_ROWS)]

    def to_pixel(self, x, y):
        """Map a window coordinate to a (col, row) pixel, or None if outside."""
        if self.xmax == self.xmin or self.ymax == self.ymin:
            return None

        if not (self.xmin <= x <= self.xmax and self.ymin <= y <= self.ymax):
            return None

        px = round((x - self.xmin) / (self.xmax - self.xmin) * MAX_COL)
        py = round((self.ymax - y) / (self.ymax - self.ymin) * MAX_ROW)
        return px, py

    def to_coord(self, px, py):
        """Map a (col, row) pixel back to a window coordinate."""
        x = self.xmin + px / MAX_COL * (self.xmax - self.xmin)
        y = self.ymax - py / MAX_ROW * (self.ymax - self.ymin)
        return x, y

    def get_pixel(self, px, py):
        return self.pixels[py][px]

    def set_pixel(self, px, py, on):
        self.pixels[py][px] = on

    def clear(self):
        self.pixels = [[False] * PIXEL_COLS for _ in range(PIXEL_ROWS)]
