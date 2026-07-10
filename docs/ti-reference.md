# TI-83 Plus / TI-84 Plus guidebook notes

Curated notes from the official **TI-84 Plus and TI-84 Plus Silver Edition Guidebook**
(`education.ti.com/html/eguides/graphing/84Plus/PDFs/TI-84-Plus-guidebook_EN.pdf`, OS
2.53MP-era, 422 pages), cross-referenced against what `src/pitybas/tokens.py` and
`CHANGELOG.md` currently implement, plus the open/completed scoping in this project's
Linear issues (the `Thomas Roten` workspace, `THO-*`).

This is **not** the TI-84 Plus CE guidebook — the CE targets a 320x240 color LCD and a
different BASIC dialect. pitybas targets the monochrome 95x63-pixel grid (confirmed by
`src/pitybas/graph.py` and `tests/circle.bas`), which is what the TI-83 Plus / TI-84 Plus
(non-CE) family shares. The guidebook explicitly notes "TI-84 Plus" in its body also
covers the TI-84 Plus Silver Edition and (per TI's separate 83 Plus guidebook, not
fetched here) the TI-83 Plus family is compatible for everything below except the
RTC-backed clock commands (`getDate`, etc.) and a few later-OS-only additions.

Page numbers below are the guidebook's own printed page numbers (footer), not PDF page
indices. Short quotes are used only where exact wording matters; everything else is
paraphrased.

---

## Window variables (Chapter 3, p.73-74; Appendix B p.398)

- **`Xmin`/`Xmax`/`Xscl`/`Ymin`/`Ymax`/`Yscl`** — implemented (`tokens.py` `GraphVar`
  subclasses). Matches the guidebook directly.
- **`Xres`** (p.73) — **not implemented in pitybas** (no `Xres` class, no `GraphState`
  attribute). Confirmed guidebook behavior:
  > "`Xres` sets pixel resolution (1 through 8) for function graphs only. The default is
  > 1. At `Xres`=1, functions are evaluated and graphed at each pixel on the x-axis. At
  > `Xres`=8, functions are evaluated and graphed at every eighth pixel along the x-axis."

  This governs automatic function-graphing sample density only (`DispGraph`/`Y=`
  plotting) — it is **not** a general drawing-resolution knob. `ZStandard` resets it to 1
  (p.83). This is in scope for the still-backlogged Linear issue **THO-18** (Phase G:
  Y1-Y9 equations). That issue's research also flags and **refutes** a claim repeated on
  some third-party calculator tutorial sites that `Xres`=1 corresponds to "133 pixels" —
  the guidebook's own `Pxl-On(`/`pxl-Test(` domain (`row` 0-62, `col` 0-94, p.132-133) and
  the ΔX accuracy formula below both put the addressable grid at 95 columns, matching
  `pitybas`'s `PIXEL_COLS = 95` exactly. Treat the "133 pixels" claim as wrong.
- **`ΔX`/`ΔY`** (p.74, confirmed via Appendix B "Accuracy Information" p.398):
  `ΔX = (Xmax - Xmin) / 94`, `ΔY = (Ymax - Ymin) / 62` in full-screen mode (there are
  separate divisors — 46 and 30/50 — for the TI's split-screen Horiz/G-T modes, which
  pitybas has no equivalent of and can ignore). This is exactly the mapping
  `GraphState.to_pixel`/`to_coord` in `src/pitybas/graph.py` already implement
  (`MAX_COL = 94`, `MAX_ROW = 62`) — **directly confirmed**, not inferred.
- **`AxesOn`/`AxesOff`** — implemented. Guidebook (p.75) confirms these are part of the
  **format** menu (`2nd [FORMAT]`), a separate settings group from window variables that
  also includes `RectGC`/`PolarGC`, `CoordOn`/`CoordOff`, `GridOff`/`GridOn`,
  `LabelOff`/`LabelOn`, and `ExprOn`/`ExprOff` — **none of which pitybas implements**
  besides `AxesOn`/`AxesOff`. Of these, `CoordOn`/`CoordOff` is explicitly relevant to the
  open free-moving-cursor work (**THO-21**, see below) and is called out there as an
  optional stretch task, default-on.
- **`ZStandard`** (p.83) and **`ZDecimal`** (p.82) — implemented. Confirmed default
  values: `ZStandard` sets `Xmin=Ymin=-10`, `Xmax=Ymax=10`, `Xscl=Yscl=1`, `Xres=1`.
  `ZDecimal` sets `Xmin=-4.7`, `Xmax=4.7`, `Ymin=-3.1`, `Ymax=3.1`, `Xscl=Yscl=1` (ΔX=ΔY=0.1).
  Other `ZOOM` menu entries (`ZBox`, `Zoom In/Out`, `ZSquare`, `ZTrig`, `ZInteger`,
  `ZoomStat`, `ZoomFit`, `ZQuadrant1`, `ZFrac1/2`...`ZFrac1/10`) are **not implemented** —
  not currently scoped in any open Linear issue found.

## Y=/equations (Chapter 3 p.66-70; not yet built — Linear THO-18, backlog)

pitybas has **zero infrastructure** for `Y1`-`Y9`/`Y0` today (no tokens, no storage). The
THO-18 issue did primary-source research before scoping the work; the key confirmed facts
(directly from the guidebook, not inferred):

- **Storing an equation requires a quoted string, not a bare expression** (p.68,
  "Defining a Function from the Home Screen or a Program"):
  > "Press `ALPHA` `["]`, enter the expression, and then press `ALPHA` `["]` again. Press
  > `STO►`." — i.e. `"X²"→Y1` (quoted), not `X²→Y1` (unquoted). The unquoted form is `ERR:DATA
  > TYPE` on real hardware per THO-18's research (the guidebook doesn't state this
  > negative case explicitly, but it's consistent with strings being the only valid
  > equation-store type; **treat this specific claim as inferred, not directly quoted**).
- **Bare `Yn` evaluates at the interpreter's current `X`; `Yn(value)` evaluates with `X`
  temporarily bound to `value`** (p.68-69, "Evaluating Y= Functions in Expressions"):
  `Yn(value)` and `Yn({value1,value2,...})` (list input &rarr; list output) are both
  directly documented.
- **Selecting/deselecting a function** (p.69) only gates automatic `DispGraph` plotting —
  a deselected `Yn` stays fully readable/callable and referenceable from other `Yn`
  definitions. Directly stated: "The TI-84 Plus graphs only the selected functions."
- **There is no interactive `Graph` token** — the programmable command that plots the
  current window + all selected `Yn` is `DispGraph` (PRGM I/O menu, not covered in the
  pages fetched here but referenced throughout Chapter 3). Pressing the physical `GRAPH`
  key is the interactive equivalent but isn't itself a program instruction.
- **Graphing a family of curves**: `{2,4,6}sin(X)` graphs three separate functions,
  `2sin(X)`, `4sin(X)`, `6sin(X)` (p.77) — this only applies to `Yn` definitions, not
  `DrawF` (`DrawF` explicitly rejects a list, see DRAW menu section below).
- **Free-moving cursor vs. TRACE** (p.78) are two distinct exploration modes:
  - *Free-moving cursor*: arrow keys move a cursor pixel-by-pixel from window-center on
    first press; coordinates shown at bottom if `CoordOn`; `CLEAR`/`ENTER` hides it and
    remembers position. Works over **any** graph-screen content, not just `Yn` — this is
    what Linear's **THO-21** (open, backlog) scopes for the `vt100` backend, since it has
    no `Yn`/Trace dependency and pitybas already supports free-drawn content (`Pt-On`,
    `Line(`, `Circle(`).
  - *TRACE*: snaps to actual sampled points along a **selected `Yn`**, moves along the
    curve with left/right and between curves with up/down. Depends on `Yn` existing
    (THO-18) — out of scope until then, and explicitly deferred as a separate future issue
    in THO-21's notes.

## DRAW menu (Chapter 8, p.121-136)

DRAW menu order, confirmed against pitybas's implementation status:

| # | Command | pitybas | Notes |
|---|---|---|---|
| 1 | `ClrDraw` | ✅ | |
| 2 | `Line(` | ✅ | `Line(X1,Y1,X2,Y2[,0])` — the guidebook documents a 5th argument, `0`, that **erases** a line segment instead of drawing it (p.124). Confirmed: pitybas's `Line.call` already accepts a 5th arg and treats `!= 0` as on/off, matching this. |
| 3 | `Horizontal` | ✅ | |
| 4 | `Vertical` | ✅ | |
| 5 | `Tangent(` | ❌ | Not implemented; no open Linear issue found scoping it. |
| 6 | `DrawF` | ✅ | Cannot take a list (family of curves) per guidebook note (p.127) — worth a regression test if not already covered. |
| 7 | `Shade(` | Partial | `Shade(lowerfunc,upperfunc[,Xleft,Xright,pattern,patres])`. `pattern` 1-4 (vertical/horizontal/-45°/+45°, default 1), `patres` 1-8 (shade every Nth pixel, default 1) (p.128). Confirmed: pitybas's `Shade` accepts this exact 2/4/6-arg signature and honors `patres` as column-sampling stride, but its own source comment admits `pattern` is accepted for signature compatibility only — every value renders as solid fill, since the real per-pattern pixel layout (vertical/horizontal/diagonal hatching) was never verified against a reference. |
| 8 | `DrawInv` | ❌ | See below — Linear THO-18 scope, unconfirmed detail. |
| 9 | `Circle(` | ✅ | `Circle(X,Y,radius)` — note the guidebook's caution that circles drawn via the *interactive* cursor are always visually circular, but `Circle(` called programmatically can look elliptical if the window isn't square (`ZSquare` first) — this is a display-shape nuance, not a pitybas bug. |
| 0 | `Text(` | Partial | See Strings/Text section below. |
| A | `Pen` | ❌ | Free-form interactive drawing tool; "You cannot execute `Pen` from the home screen or a program" (p.130) — **not programmable at all** on real hardware, so it is fundamentally out of scope for a headless interpreter, not a gap. |

**`DrawInv`** (p.127, `DRAW` menu item 8): directly confirmed facts —
> "`DrawInv` (draw inverse) draws the inverse of *expression* by plotting X values on the
> y-axis and Y values on the x-axis... `DrawInv` is not interactive. `DrawInv` works in
> Func mode only." Also: "You cannot use a list of *expressions* with `DrawInv`."

What the guidebook does **not** state, and THO-18 flags explicitly as an **inferred, not
confirmed** implementation detail: whether `DrawInv` samples at `Xres`-gated intervals
(like automatic `Yn` graphing) or at every pixel column unconditionally (like `DrawF`,
which is `Xres`-independent per p.127's `DrawF` note plus this project's Phase D work).
THO-18 recommends the `DrawF`-style every-column sampling by analogy but marks it a
guess. Also note: "`DrawInv` is valid only in Func graphing" (p.123) — since pitybas has
no Par/Pol/Seq graphing-mode concept, this constraint is moot/always-satisfied here.

Also note from p.122 ("Before Drawing on a Graph"): **any** `DRAW` output is temporary —
changing window vars, mode/format settings, or the `Yn` selection set silently discards
prior `DRAW` output on next display (matches `ClrDraw`'s described behavior; `StorePic`
is the only way to persist drawings across such a change).

### DRAW POINTS submenu (p.131-133)

`Pt-On(`/`Pt-Off(`/`Pt-Change(` (point ops, optional `mark` arg: 1=dot default, 2=box,
3=cross) and `Pxl-On(`/`Pxl-Off(`/`Pxl-Change(`/`pxl-Test(` (raw pixel ops, no mark arg)
— all implemented in pitybas. Confirmed domains, **directly settling the Xres/pixel-count
question above**:
> "`Pxl-On(` (pixel on) turns on the pixel at (*row*,*column*), where *row* is an integer
> between 0 and 62 and *column* is an integer between 0 and 94."

This is unambiguous primary-source confirmation of the 95(col)x63(row) grid pitybas
already uses — there is no ambiguity or "133 pixels" alternative reading in the official
guidebook.

### DRAW STO submenu / GDB (p.134-136)

`StorePic`/`RecallPic`/`StoreGDB`/`RecallGDB` — all implemented (slots 0-9, matching the
guidebook's `Pic0`-`Pic9`/`GDB0`-`GDB9` numbering).

**A GDB stores exactly five things** (p.135, directly quoted list):
1. Graphing mode
2. Window variables
3. Format settings
4. All functions in the Y= editor **and the selection status of each**
5. Graph style for each Y= function

> "GDBs do not contain drawn items or stat plot definitions."

pitybas's current `GDB_ATTRS` tuple (`tokens.py`) only covers window variables +
`axes_on` (item 2 + one format setting) — items 1, 3 (mostly), 4, and 5 are all
unimplemented, consistent with no `Yn`/graphing-mode/graph-style infrastructure existing
yet. The code already has a comment anticipating this: *"Extend this tuple to include
equation state once Y1-Y9 equations exist."* This is exactly Linear **THO-18**'s scope.

**`RecallGDB` fully replaces, does not merge**, confirmed directly:
> "CAUTION: When you recall a GDB, it replaces all existing Y= functions. Consider
> storing the current Y= functions to another database before recalling a stored GDB."

`StorePic`/`RecallPic`: a picture "includes drawn elements, plotted functions, axes, and
tick marks" but **not** axis labels, bound indicators, prompts, or cursor coordinates
(p.134) — a nuance for anything comparing pitybas's pixel-buffer-only `Pic` snapshot
against real hardware.

### Placing text on a graph (p.129) — `Text(`

Directly confirmed domain, matching pitybas's `TEXT_MAX_ROW`/`MAX_COL` constants exactly:
> "The top-left corner of the first character is at pixel (*row*,*column*), where *row*
> is an integer between 0 and 57 and *column* is an integer between 0 and 94."

Also confirmed: `value` can be a literal quoted string **or an expression** (evaluated
and displayed with up to 10 characters) — `Text(row,col,value,value,...)` accepts
multiple values concatenated. The guidebook doesn't specify column-overflow behavior
beyond "the font is proportional, so the exact number of characters you can place on the
graph varies" — no explicit "clips" vs. "wraps" statement in the pages fetched; treat any
clip-vs-wrap claim (e.g. in Linear THO-22's notes) as inferred/researched-elsewhere, not
a guidebook quote.

pitybas's `Text(` (per README's Known Limitations) validates arguments and calls
`draw_text_graph`, but **no backend actually renders glyphs yet** — Braille's 2x4 dot
resolution is too coarse for legible small-font text at native size (confirmed by
prototyping notes in Linear **THO-16**/**THO-22**, which tried rasterizing at native and
2x native size and found both illegible; the planned fix is to stamp literal characters
onto the nearest Braille cell instead of dot-packing them — **THO-22**, still open).

## Lists (Chapter 11, p.161-176)

- **Names**: `L1`-`L6` built in; user-created names 1-5 chars, must start with a letter
  or θ. Max list dimension: **999 elements** (p.163) — not enforced/tested in pitybas as
  far as this research determined; worth a bounds check if strict TI parity matters.
- **`L` prefix**: the small-capital `L` glyph before a user-created list name
  disambiguates it from implied multiplication in contexts where a list name isn't the
  only valid input (e.g. home screen) — not needed at STAT-editor-only prompts. pitybas
  already supports this (CHANGELOG 0.4.1/0.5.1: uppercase `L`, lowercase `l`, `∟` glyph,
  and Unicode subscript digits like `L₁` all treated as equivalent).
- **Complex-number lists**: storing one complex element converts the **whole list** to
  complex; `real(listname)→listname` converts back (p.163). pitybas has no complex-number
  support at all (see `TODO.md`), so this is moot until that lands.
- **Implemented list ops** (LIST OPS menu, p.168-174): `SortA(`/`SortD(`, `dim(`, `Fill(`,
  `seq(`, `cumSum(`, `ΔList(`, `augment(` — confirmed present in pitybas. **`Select(`**
  (interactive stat-plot point picker) and **`List►matr(`/`Matr►list(`** (list/matrix
  conversion) are **not implemented** — no Linear issue found scoping them; `Select(`
  is inherently interactive/stat-plot-dependent and may not translate to a headless
  interpreter at all.
- **LIST MATH menu** (p.175-176): `min(`/`max(` (pitybas: `Min`/`Max` tokens, confirmed),
  `mean(`, `median(`, `sum(`/`prod(` (confirmed present), `stdDev(`, `variance(` — the
  last four (`mean`, `median`, `stdDev`, `variance`) are **not implemented** in pitybas;
  no open Linear issue found. `sum(`/`prod(` both take optional `[start,end]` range args
  (p.176) — verify pitybas's implementations accept these, not just whole-list.
- **`nPr`/`nCr` list-argument support** (referenced generically by "you can use a list to
  input several values for some math functions", p.167) is exactly Linear **THO-32**
  (open, backlog): `nPr`/`nCr` in `tokens.py` are scalar-only via `math.factorial` today.

## Matrices (Chapter 10, p.143-158)

- Matrix variables `[A]`-`[J]`, up to 99x99 (memory permitting), **real numbers only** —
  "You can store only real numbers in TI-84 Plus matrices" (p.145). pitybas has no
  complex-number support anyway, so this constraint is currently moot.
- Confirmed operators/functions: `+`/`-`/`*` (dimension-matched), negation, `abs(`,
  `round(matrix[,#decimals])`, `-1` inverse (`x⁻¹` or `^-1`, square matrices only,
  determinant ≠ 0), integer powers 0-255, `=`/`≠` (element-wise, all-true/any-false
  semantics), `iPart(`/`fPart(`/`int(`, `det(`, `T` (transpose), `dim(`, `Fill(`,
  `identity(`, **`randM(rows,cols)`** (confirmed: "returns integers ≥ -9 and ≤ 9",
  p.156 — matches the range noted in Linear **THO-32**'s sibling context and worth
  checking pitybas's `randM` implementation against exactly), `augment(`,
  `Matr►list(`/`List►matr(`, `cumSum(`, and row-ops `ref(`/`rref(`/`rowSwap(`/`row+(`/
  `*row(`/`*row+(`.
- Grep of `tokens.py`'s `Matrix` class shows it as a bare `Variable`/`Stub` — i.e.
  pitybas currently models matrix **storage** but this research did not confirm how much
  of the above math-function list is actually wired up to matrix operands (vs.
  list/scalar only). Worth an explicit audit before assuming parity; not covered by any
  open Linear issue found.

## Strings (Chapter 15, p.266-274)

Directly confirmed: **there are exactly six string functions**, and they exist **only in
the CATALOG** (not on any dedicated keyboard menu):

| Guidebook name | pitybas | Notes |
|---|---|---|
| `Equ►String(` | ❌ | Converts a `Yn` equation to a string. Blocked on `Yn` existing (THO-18). |
| `expr(` | ✅ | "converts the character string...to an expression and executes it" — matches pitybas's `expr(`. |
| `inString(` | ⚠️ Bug | `inString(string,substring[,start])`. Guidebook (p.271) directly confirms: `start` is **1-based** (default 1), and the returned position is **1-based**; "If *string* does not contain *substring*, or *start* is greater than the length of *string*, `inString(` returns **0**." Reading `tokens.py`'s `inString.call` directly: it does `haystack.find(needle, skip)` and returns the raw result — Python's `str.find` is 0-based on both the start-offset and the returned index, and returns **-1** (not 0) when the substring isn't found, and it is never given a `-1` adjustment for the 1-based `start` argument either. Concretely: `inString("PQRSTUV","STU")` should return `4` per the guidebook's own worked example (p.271) but pitybas returns `3`; a not-found search returns `-1` instead of `0`. No existing test (`grep inString tests/` is empty) caught this — genuinely unconfirmed/wrong until this pass, not just a documentation gap. |
| `length(` | ✅ | Confirmed: an instruction/function name like `sin(` counts as **one** character toward length — an easy-to-miss edge case worth a regression test if not already covered. |
| `String►Equ(` | ❌ | Inverse of `Equ►String(`; also blocked on `Yn`. |
| `sub(` | ✅ | `sub(string,begin,length)` — confirmed pitybas's `sub` token matches this 3-arg, 1-based-begin form. |

**`toString(` is not a real TI-83/84 Plus command.** It does not appear anywhere in this
guidebook's CATALOG string-function list (which is exhaustive — "the six string
functions"), its alphabetical CATALOG listing, or its index. pitybas added `toString(` in
CHANGELOG 0.4.0 ("converts a real number to its string representation... for
concatenation into `Disp`/`Output` strings") — this is a **plausible but unconfirmed
invention**, or possibly back-ported from the TI-84 Plus CE dialect (which does have a
real `toString(`, added in a later CE-only OS). Since this project explicitly targets the
non-CE 95x63 family (per `AGENTS.md`/`tests/circle.bas`), **`toString(` should be flagged
as a deliberate compatibility deviation, not assumed to be authentic TI-83/84 Plus
behavior** — worth a doc comment or README callout if not already present.

Also confirmed (p.267): a string is entered/closed with `ALPHA ["]` on both ends; a
blank space is a distinct character (`ALPHA [␣]`); concatenation uses `+` between two
strings or string variables, chainable (p.270).

## Error messages (Appendix B, p.394-397)

Every `ERR:` string pitybas currently raises (grepped from `src/pitybas`) matches an
official TI-84 Plus error type name exactly: `DATA TYPE`, `DIM MISMATCH`, `DOMAIN`,
`NONREAL ANS`, `ARGUMENT`, `UNDEFINED`. No fabricated error names found — good parity.
Errors pitybas does not yet raise anywhere (e.g. `ERR:INVALID DIM`, `ERR:SINGULAR MAT`,
`ERR:BOUND`) are simply cases pitybas hasn't hit yet (many, like `STAT`/`ZOOM`/link
errors, are inapplicable to a headless interpreter).

## Accuracy information (Appendix B, p.398-399)

- Real hardware stores values internally with **up to 14 digits and a 2-digit exponent**,
  more precision than it displays (max 10 displayed digits). This is the real-hardware
  analog of the float-precision question raised in Linear **THO-33** (`VM.get()`: whole-
  number floats collapse to `int` with no rounding tolerance) — the guidebook doesn't
  prescribe an exact tolerance for that specific coercion, so THO-33 remains an open
  design question, not something this guidebook settles.
- Trig/inverse-trig, log, exponential, and hyperbolic function domains are all tabulated
  precisely (p.399) — e.g. `sin`/`cos`/`tan`: `0 ≤ |x| < 10^12`; `sin⁻¹`/`cos⁻¹`:
  `-1 ≤ x ≤ 1`; `x!`: `-.5 ≤ x ≤ 69`, x a multiple of .5. Not cross-checked in detail
  against pitybas's own domain validation in this pass — worth a follow-up audit if exact
  overflow/domain-error parity matters.
- `minimum`/`maximum` (CALC menu) tolerance: `1E-5`; `∫f(x)dx`: `1E-3`. Not applicable to
  pitybas (no CALC menu / numerical calculus operations implemented).

## Inverse trig unicode tokens (Chapter 2; Linear THO-31, open backlog)

The guidebook's CATALOG lists hyperbolic inverses using the real superscript-minus-one
glyph form: `sinh⁻¹(`, `cosh⁻¹(`, `tanh⁻¹(` (p.273-274, confirmed via rendered CATALOG
table). pitybas's hyperbolic inverses already use this (CHANGELOG 0.4.0 fixed a token
collision there), but `asin`/`acos`/`atan` in `tokens.py` still key off the placeholder
ASCII strings `"sin-1"`/`"cos-1"`/`"tan-1"` instead of the real `sin⁻¹(`/`cos⁻¹(`/
`tan⁻¹(` glyphs — this is exactly THO-31's open scope. This guidebook excerpt doesn't
independently settle the *inverse trig* (non-hyperbolic) glyph spelling since the pages
fetched here covered CATALOG hyperbolic entries, not the ANGLE/TEST menu inverse-trig
entries directly — treat the non-hyperbolic glyph identity as consistent-by-analogy
rather than independently re-confirmed in this pass.

## PRGM CTL / PRGM I/O (Chapter 16, p.281-294)

The `PRGM` key's two token menus, in guidebook order, confirmed against pitybas:

**PRGM CTL** (`PRGM` from the program editor, p.281):

| # | Command | pitybas | Notes |
|---|---|---|---|
| 1 | `If` | ✅ | |
| 2 | `Then` | ✅ | |
| 3 | `Else` | ✅ | |
| 4 | `For(` | ✅ | |
| 5 | `While` | ✅ | |
| 6 | `Repeat` | ✅ | |
| 7 | `End` | ✅ | |
| 8 | `Pause` | ✅ | Optional `value` arg to display and scroll (p.284) — not cross-checked for exact parity in this pass. |
| 9 | `Lbl` | ✅ | |
| 0 | `Goto` | ✅ | |
| A | `IS>(` | ✅ | `tokens.py`'s `IsGreaterThanSkip`, `token = "IS>"` — matches `IS>(variable,value)` exactly (p.286). |
| B | `DS<(` | ✅ | `tokens.py`'s `DsLessThanSkip`, `token = "DS<"` — matches `DS<(variable,value)` exactly (p.286). |
| C | `Menu(` | ✅ | |
| D | `prgm` | ✅ | |
| E | `Return` | ✅ | |
| F | `Stop` | ✅ | |
| G | `DelVar` | ✅ | |
| H | `GraphStyle(` | ❌ | `GraphStyle(function#,graphstyle#)` sets a `Yn` function's draw style (1=line...7=dot, p.287-288) — genuinely missing (`grep -n "GraphStyle" src/pitybas/tokens.py` finds nothing, and it's not mentioned in `TODO.md`/`CHANGELOG.md`). Blocked on `Y1`-`Y9` existing (Linear **THO-18**); GDB's 5th stored element ("graph style for each Y= function", see DRAW/GDB section above) also depends on this. |
| I | `OpenLib(` | ❌ | Guidebook itself says "No longer used" (p.281) — dead on real hardware too, not a real gap. |
| J | `ExecLib(` | ❌ | Same as `OpenLib(` — "No longer used." |

**PRGM I/O** (`PRGM` ▶ from the program editor, p.288):

| # | Command | pitybas | Notes |
|---|---|---|---|
| 1 | `Input` | ✅ | |
| 2 | `Prompt` | ✅ | |
| 3 | `Disp` | ✅ | |
| 4 | `DispGraph` | ❌ | Displays the current graph (p.291) — genuinely missing (no class in `tokens.py`). This is exactly Linear **THO-18**'s task 2, which explicitly renames its originally-scoped `Graph` token to the real `DispGraph` name once it lands. |
| 5 | `DispTable` | ❌ | pitybas has **no Table subsystem at all** — no `TblStart`/`ΔTbl`, nothing from Chapter 7 ("Tables", p.115-118) is implemented, and it isn't mentioned in `TODO.md` or any open Linear issue found. `DispTable` is blocked on that entire feature. |
| 6 | `Output(` | ✅ | `Output(row,column,value)`, row 1-8, column 1-16 (p.291) — domain bounds not cross-checked against pitybas's implementation in this pass. |
| 7 | `getKey` | ✅ | Key-code diagram (p.292) not cross-checked against pitybas's key-code constants in this pass. |
| 8 | `ClrHome` | ✅ | |
| 9 | `ClrTable` | ❌ | Same Table-subsystem gap as `DispTable`. |
| 0 | `GetCalc(` | ❌ | Calculator-to-calculator variable transfer over USB/I/O port (p.292-293). No other calculator exists in a headless interpreter — plausibly out-of-scope-by-design rather than a real gap, similar to `Pen` (see DRAW menu section above), but flagging it here since it wasn't previously noted anywhere. |
| A | `Get(` | ❌ | Reads data from a CBL2/CBR probe device (p.293) — same "no physical device to talk to" reasoning as `GetCalc(`. |
| B | `Send(` | ❌ | Sends data to a CBL2/CBR probe device (p.293) — same reasoning. |

## Not covered in this pass

Time/scope-boxed this research to the topics above (matching `AGENTS.md`'s list plus the
open Linear scope). Not fetched from the guidebook in this pass, and therefore **not**
verified against primary source: polar/rectangular conversions (`R►Pr(`, `R►Pθ(`,
`P►Rx(`, `P►Ry(`, `Angle(` — noted in `TODO.md` as unimplemented, angle-mode-dependent,
no equivalent in pitybas), `►DMS` display conversion (also in `TODO.md`), complex-number
mode and `►Polar`/`re^θi` display, Chapter 7 (Tables, entirely unimplemented — see PRGM
I/O section above), and the RTC clock chapter (already landed per CHANGELOG 0.5.0, not
re-verified here).
