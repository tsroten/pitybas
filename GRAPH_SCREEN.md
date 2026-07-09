# TI-84+ Graph Screen Implementation Requirements

This document describes what a full-fledged TI-84+ graph screen implementation
would need for a TI-Basic interpreter such as pitybas.

## Current State

pitybas has **zero graph screen support**. The IO backend (`IOBase`) handles
only text-mode operations (`disp`, `output`, `input`, `getkey`, `pause`,
`menu`, `clear`). No graph drawing tokens exist in `tokens.py`.

---

## 1. Screen Model

- **Resolution:** 96 × 64 pixels (columns 0–95, rows 0–63; row 0 = top).
- **Two separate buffers** tracked independently:
  - A **pixel/drawing buffer** — cleared by `ClrDraw`.
  - A **function/equation buffer** — cleared by `ClrGraph`.
- **Graph database (GDB):** window settings + equation state, saved/restored
  with `StoreGDB`/`RecallGDB`.
- **Picture slots (Pic0–Pic9):** full-screen pixel snapshots, saved/restored
  with `StorePic`/`RecallPic`.

---

## 2. Window State Variables

Seven system variables map math coordinates to screen pixels.

| Variable | Default | Meaning                              |
|----------|---------|--------------------------------------|
| `Xmin`   | −10     | Left edge of window                  |
| `Xmax`   | 10      | Right edge of window                 |
| `Xscl`   | 1       | X-axis tick spacing                  |
| `Ymin`   | −10     | Bottom edge of window                |
| `Ymax`   | 10      | Top edge of window                   |
| `Yscl`   | 1       | Y-axis tick spacing                  |
| `Xres`   | 1       | Pixel resolution for graphing (1–8)  |

### Coordinate Mapping

**Math → pixel:**

```
xp = floor((x - Xmin) / (Xmax - Xmin) * 95)
yp = floor(63 - (y - Ymin) / (Ymax - Ymin) * 63)
```

**Pixel → math (inverse):**

```
x = Xmin + xp * (Xmax - Xmin) / 95
y = Ymin + (63 - yp) * (Ymax - Ymin) / 63
```

---

## 3. New Tokens Required

### Screen Control

| Token         | Description                                      |
|---------------|--------------------------------------------------|
| `DispGraph`   | Refresh/show the graph screen.                   |
| `ClrDraw`     | Clear drawn objects (not graphed functions).     |
| `ClrGraph`    | Clear graphed functions.                         |
| `AxesOn`      | Enable axes display.                             |
| `AxesOff`     | Disable axes display.                            |

### Point Drawing (math coordinates)

| Token                  | Description                               |
|------------------------|-------------------------------------------|
| `Pt-On(x, y[, mark])`  | Draw a point.                             |
| `Pt-Off(x, y[, mark])` | Erase a point.                            |
| `Pt-Change(x, y[, mark])` | Toggle a point.                        |

Mark values:

| Value | Symbol               |
|-------|----------------------|
| 1     | Filled square (dot, default) |
| 2     | Open square          |
| 3     | Cross (+)            |
| 4     | Filled square, larger|
| 5     | Open square, larger  |

### Raw Pixel Drawing (pixel coordinates, row/col order)

> **Note:** Pixel commands use **row, col** order — the opposite of X, Y.
> Valid range: row 0–63, col 0–95.

| Token                  | Description                                        |
|------------------------|----------------------------------------------------|
| `Pxl-On(row, col)`     | Turn on a pixel.                                   |
| `Pxl-Off(row, col)`    | Turn off a pixel.                                  |
| `Pxl-Change(row, col)` | Toggle a pixel.                                    |
| `Pxl-Test(row, col)`   | Return 1 if pixel is on, 0 if off (expression).   |

### Geometric Drawing (math coordinates)

| Token                          | Description                                           |
|--------------------------------|-------------------------------------------------------|
| `Line(x1, y1, x2, y2[, erase])` | Draw (or erase) a line segment; 5th arg 0 = erase.  |
| `Horizontal y`                 | Full-width horizontal line at math coordinate y.      |
| `Vertical x`                   | Full-height vertical line at math coordinate x.       |
| `Circle(x, y, r)`              | Circle centred at (x, y) with radius r.               |

### Shading

| Token | Description |
|-------|-------------|
| `Shade(Ylower, Yupper[, Xmin, Xmax, pattern, patres])` | Shade the region between two expressions. |

### Text on Graph Screen (pixel coordinates)

- `Text(row, col, expr[, expr, ...])` — render text at the given pixel
  position using the built-in 6×8 px font.
  - Valid rows: 0–57; valid columns: 0–91.
- `Text(-1, row, col, expr[, ...])` — small-font variant (some OS versions).

### Function Graphing

| Token          | Description                                |
|----------------|--------------------------------------------|
| `DrawF expr`   | Draw any expression as Y(X).               |
| `DrawInv expr` | Draw the inverse of an expression (swap X/Y). |
| `Graph`        | Graph all enabled Y= functions using the current window and Xres. |

### Picture / GDB Persistence

| Token          | Description                                     |
|----------------|-------------------------------------------------|
| `StorePic n`   | Save the full pixel buffer to picture slot n (0–9). |
| `RecallPic n`  | Restore picture slot n to the pixel buffer.     |
| `StoreGDB n`   | Save window settings and equations to GDB slot n (0–9). |
| `RecallGDB n`  | Restore GDB slot n.                             |

---

## 4. Equation / Function State (Y= Variables)

- `Y1`–`Y9`, `Y0` — ten function slots; each stores a callable expression or
  `None`.
- Must support assigning an expression (`Y1 = X²`) and then graphing it with
  `DrawF Y1` or `Graph`.
- `Graph` iterates all enabled Y= slots, samples X from Xmin to Xmax in steps
  of `(Xmax - Xmin) / 95 * Xres`, and plots each result.

---

## 5. IO Backend Extensions

`IOBase` needs new abstract methods (or an opt-in `GraphIOBase` mixin) to
support graph operations:

```python
def disp_graph(self): ...              # flush/show the pixel buffer
def clr_draw(self): ...                # clear the drawing layer
def pxl_on(self, row, col): ...
def pxl_off(self, row, col): ...
def pxl_change(self, row, col): ...
def pxl_test(self, row, col) -> int: ...
def draw_line(self, x1, y1, x2, y2, erase=False): ...
def draw_circle(self, x, y, r): ...
def draw_text_graph(self, row, col, text): ...
# StorePic / RecallPic, StoreGDB / RecallGDB, Shade, DrawF, DrawInv ...
```

The VM also needs to expose `Xmin`, `Xmax`, `Ymin`, `Ymax`, `Xscl`, `Yscl`,
and `Xres` as first-class readable/writable system variables.

---

## 6. Coordinate Edge Cases

- Out-of-bounds drawing calls must **clip silently** to screen edges; they must
  not raise an error.
- `Pxl-*` commands use **row, col** order (row = Y-pixel from top); `Pt-*` and
  geometric commands use **math X, Y** order.
- `Text` on the graph screen uses **pixel row/col**, not math coordinates.
- `Line` with a 5th argument of `0` erases rather than draws.

---

## 7. Suggested Implementation Order

1. **Window variables** — add `Xmin`, `Xmax`, `Ymin`, `Ymax`, `Xscl`, `Yscl`,
   `Xres` to the VM as system variables with TI-84+ defaults.
2. **Pixel buffer** — internal 96×64 bit array; implement `DispGraph`,
   `ClrDraw`, `AxesOn`/`AxesOff`.
3. **Raw pixel ops** — `Pxl-On`, `Pxl-Off`, `Pxl-Change`, `Pxl-Test`.
4. **Point ops** — `Pt-On`, `Pt-Off`, `Pt-Change` (delegate to pixel ops via
   coordinate mapping).
5. **Geometric drawing** — `Line`, `Horizontal`, `Vertical`, `Circle`.
6. **Text on graph** — `Text(row, col, ...)`.
7. **Function graphing** — Y= variable slots, `DrawF`, `DrawInv`, `Graph`,
   `ClrGraph`.
8. **Persistence** — `StorePic`/`RecallPic`, `StoreGDB`/`RecallGDB`.
9. **Advanced** — `Shade`, `DrawPolar`, `DrawParam`.
