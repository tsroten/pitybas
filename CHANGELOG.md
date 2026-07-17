# Changelog

## Unreleased

### Added
- Added logarithmic and exponential functions `ln(`, `log(`, `logBASE(`, `e^(`, and `10^(` with scalar and List support.
- Added numerical calculus/root-finding functions, each evaluating an expression in terms of a bound variable: `nDeriv(expr,var,value[,H])` (symmetric-difference derivative, `H` defaults to `1e-3`), `fnInt(expr,var,lower,upper[,tol])` (adaptive Simpson's-rule definite integral, `tol` defaults to `1e-5`), `fMax(expr,var,lower,upper[,tol])`/`fMin(...)` (golden-section extrema search returning the maximizing/minimizing variable value), and `solve(expr,var,guess[,{lower,upper}])` (root finder for `expr = 0`, bisecting a sign change found either directly in `{lower,upper}` or by searching outward from `guess`; bounds default to the TI-84's own `{-1E99,1E99}` when omitted, and `ERR:NO SIGN CHNG` is raised whenever `expr` never changes sign in range — matching real hardware, e.g. `solve(X^2,X,1)` always raises this since `X^2` never crosses zero). Every numeric argument (and the bound expression's result) is validated as a real scalar, raising `ERR:DATA TYPE`/`ERR:NONREAL ANS` for List/Matrix or non-real-complex values instead of leaking a raw Python `TypeError`
- Added `remainder(dividend,divisor)`, the whole-number remainder using truncated (toward-zero) division so the result carries the dividend's sign, with element-wise List broadcasting (`remainder(list,divisor)`, `remainder(dividend,list)`, and same-length `remainder(list,list)`); raises `ERR:DIVIDE BY 0` for a zero divisor, `ERR:DIM MISMATCH` for mismatched list lengths, and `ERR:DATA TYPE` for Matrix operands (unsupported on real hardware, like `nPr`/`nCr`)
- Added the list summary-statistics functions `mean(`, `median(`, `stdDev(`, and `variance(`, each accepting an optional `freqlist` weighting argument (e.g. `mean(∟L,∟F)`). Following real TI-83/84 behavior, `stdDev(`/`variance(` return the *sample* statistics (dividing by `n-1`); `median(` expands values by their (integer) frequencies before taking the middle value
- Added the `1-Var Stats [Xlist[,freqlist]]` and `2-Var Stats [Xlist,Ylist[,freqlist]]` commands, which populate the standard STAT result variables readable as tokens afterwards: `1-Var Stats` sets `x̄`, `Σx`, `Σx²`, `Sx`, `σx`, `n`, `minX`, `Q1`, `Med`, `Q3`, `maxX` (quartiles use TI's median-of-halves method); `2-Var Stats` sets the `x`/`y` moment variables (`x̄`/`ȳ`, `Σx`/`Σy`, `Σx²`/`Σy²`, `Sx`/`Sy`, `σx`/`σy`, `minX`/`minY`, `maxX`/`maxY`), plus `Σxy` and `n`. Both default to `L1` (and `L2`) when called without arguments
- Added the `⁻¹` postfix operator (multiplicative inverse): `n⁻¹` evaluates to `1/n`
- Added the `×√` infix operator (general nth root): `n×√x` evaluates to the nth root of x
- Added graph screen support: a 95x63-pixel `GraphState` with window variables (`Xmin`/`Xmax`/`Xscl`/`Ymin`/`Ymax`/`Yscl`/`AxesOn`/`AxesOff`), point/pixel drawing (`Pt-On(`/`Pt-Off(`/`Pt-Change(`/`Pxl-On(`/`Pxl-Off(`/`Pxl-Change(`/`Pxl-Test(`/`ClrDraw`), geometric drawing (`Line(`, `Circle(`, `Horizontal`, `Vertical`), function/region plotting (`DrawF`, `Shade(`), text placement (`Text(`), and zoom presets (`ZStandard`, `ZDecimal`). The `vt100` IO backend (`pb -i vt100`) renders the graph screen live as a 48x16 grid of Unicode Braille characters and holds the screen at program exit if it was the most recently active screen, matching real TI-83/84 behavior; the `simple` backend and `ScriptedIO` track pixel state without rendering (see README "Known Limitations" — `Text(` doesn't render visibly under any backend yet)
- Added `StorePic`/`RecallPic` and `StoreGDB`/`RecallGDB` to snapshot the pixel buffer and graph window variables to/from numbered slots (0-9)
- Added `ScriptedIO`, a public `pitybas.io` backend for headlessly driving a program in tests and asserting on what it displayed/drew (replaces the test-only `MockIO`)
- Added an `IOBase` abstract base class formalizing the IO backend contract shared by `simple`/`vt100`/`ScriptedIO`

- Added Function-mode graph equations `Y1`-`Y9`/`Y0`, each storing an *unevaluated* expression set by storing a **string** (`"X²→Y1`, quoted — storing a bare numeric/expression value raises `ERR:DATA TYPE`, matching real hardware). Each slot behaves as both a bare variable (`Y1` re-evaluates its expression against the current `X`, save/restoring `X` like `DrawF`) and a callable function (`Y1(5)` evaluates with `X` temporarily bound to `5`), supporting cross-reference (`"-Y1→Y2`), combination (`"Y1+Y2→Y3`), and composition (`"Y1(Y2)→Y3`). Each slot carries an independent enabled/disabled selection flag (defaulting to enabled when defined) that gates automatic plotting only — a deselected slot stays fully evaluable and referenceable
- Added `FnOn`/`FnOff` to select/deselect graph equations (`FnOff` alone deselects all, `FnOff 1,3` deselects the listed ones) without deleting their definitions
- Added `DispGraph`, which resamples every *enabled* `Y1`-`Y9`/`Y0` function across the window and plots each result, sampling pixel columns 0-94 at a stride of `Xres` (`x_step = ((Xmax - Xmin) / 94) * Xres`); disabled and undefined slots draw nothing
- Added `DrawInv <expr>`, which draws the inverse of an expression (its reflection across `y = x`) by plotting each sampled point with its x/y roles swapped; like `DrawF` it samples every pixel column and ignores `Xres`
- Added `Xres` as a window variable (integer 1-8, default 1, `ERR:DOMAIN` otherwise) backed by `GraphState`; it governs `DispGraph`'s sampling stride and round-trips through `StoreGDB`/`RecallGDB` alongside the other window vars
- Extended `StoreGDB`/`RecallGDB` to snapshot and restore all 10 `Y1`-`Y9`/`Y0` equation definitions and their selection flags alongside the window variables; `RecallGDB` fully replaces the Y= functions (not a merge), so a slot blank at store-time — or one defined after the store — is cleared on recall, matching real hardware

### Changed
- Bumped supported Python versions to 3.11–3.14 (`requires-python = ">=3.11"`), updated Trove classifiers, updated mypy target to 3.11, and updated GitHub Actions test matrix and build/lint/publish jobs to target 3.11–3.14

### Fixed
- Fixed the string-store shorthand `"<text>→<var>` (unclosed quote) tokenizing the `→` and destination as part of the string literal instead of storing: `→` (STO) now terminates an unclosed string, so `"HELLO→Str1` stores `HELLO`, matching real hardware's optional closing quote
- Fixed `nPr` and `nCr` to support scalar/list broadcasting and pairwise same-length list arguments while rejecting mismatched list dimensions (`ERR:DIM MISMATCH`) and matrix operands (`ERR:DATA TYPE`); they now also return `0` when `r > n` (matching real hardware) and raise `ERR:DOMAIN` for negative or non-integer arguments instead of leaking a raw Python `factorial()` error
- Fixed `inString(` using Python's 0-based indexing and `-1` not-found sentinel instead of TI's 1-based semantics: a match now returns a 1-based character position (e.g. `inString("PQRSTUV","STU")` returns `4`), the optional `start` argument is interpreted as a 1-based position, a missing substring (or a `start` past the end of the string) returns `0` rather than `-1`, and a `start` below `1` now raises `ERR:DOMAIN` instead of being passed through as a negative (search-from-end) offset
- Fixed the `×√` operator returning floating-point noise for perfect roots (e.g. `3×√1000` now returns exactly `10`) and raising a Python complex-number error instead of `ERR:NONREAL ANS` for even roots of negative numbers
- Fixed `StorePic`/`RecallPic`/`StoreGDB`/`RecallGDB` raising a bare `AssertionError` (silently disabled under `python -O`) instead of `ERR:DOMAIN` for out-of-range or non-integer slot numbers
- Fixed parser dropping subtraction after postfix operators (`²`, `³`, `⁻¹`, `!`): `-` immediately following a postfix token was incorrectly lexed as the sign of a negative-number literal instead of a subtraction operator, so e.g. `X²-4` evaluated as `X²` alone (returning 9 for X=3 instead of 5)
- Fixed a latent mutable-default-argument bug in `Repl.__init__` where multiple `Repl()` instances created without an explicit `code` argument would share the same underlying list
- Fixed `Menu(`'s option lookup list not being reset between retry iterations: after one invalid choice, a 2-item menu's lookup held 4 entries, making an out-of-range choice like `3` silently valid and resolve to the wrong label
- Fixed `Parser.close_brackets()` (implicitly closes unclosed parens at end of line/before `->`) re-appending an already-absorbed `FunctionArgs` object, duplicating nested unclosed function calls (e.g. `max(0,abs(R->R`) and raising a spurious "bad token order" error
- Fixed `GraphState.to_pixel` raising `ZeroDivisionError` for a collapsed window (`Xmin`==`Xmax` or `Ymin`==`Ymax`); now returns `None` instead
- Fixed `Circle(`'s pixel sampling under-sampling (visible gaps) when the window's Y scale yields a larger pixel radius than X, and potentially exploding its step count when `Xmax`-`Xmin` is tiny
- Fixed `Pxl-On(`/`Pxl-Off(`/`Pxl-Change(`/`Pxl-Test(` crashing with `TypeError` on non-integer row/col arguments instead of rounding to the nearest pixel
- Fixed the vt100 backend leaving the terminal cursor hidden on exit if a keypress wait for a held graph screen was interrupted (e.g. Ctrl-C)
- Fixed the vt100 backend's exit-hold logic to track whichever screen (text or graph) was most recently active, rather than whether the graph buffer had anything drawn to it — matches verified real-hardware behavior where a later `Disp`/`Output(`/etc. switches back to the text screen and nothing holds

## 0.5.1 (2026-07-06)

### Fixed
- Fixed lists to support using the small-capital L glyph

## 0.5.0 (2026-07-06)

### Added
- Added the TI-84's RTC-backed date/time commands: `getDate`/`getTime` (read the current date/time), `setDate(`/`setTime(` (set it), `getDtFmt`/`setDtFmt(`/`getTmFmt`/`setTmFmt(` (date/time display format settings), `getDtStr(`/`getTmStr(` (formatted date/time strings), `startTmr`/`checkTmr(` (elapsed-time timer), and `timeCnv(` (seconds to `{days,hours,minutes,seconds}`)

### Fixed
- Fixed the vt100 `IO` backend's `getkey()` always returning `0` for the Enter key: `VT.getch()` translates arrow-key escape sequences to name strings (`'up'`, `'down'`, ...) for the `keycodes` lookup, but returned the raw `'\r'` byte for Enter instead of translating it to `'enter'`, so it never matched the `keycodes` dict

## 0.4.1 (2026-07-06)

### Fixed
- Lists can now be specified using Unicode subscript digits (e.g. `L₁`), the standard TI-84 plaintext representation of the default list names; `L₁` is treated as identical to `L1` and `l1`

## 0.4.0 (2026-07-06)

### Added
- Added DMS (degrees-minutes-seconds) angle literals, e.g. `30°15'20"`, which now parse and evaluate to decimal degrees (converting to radians in Radian mode, same as the standalone `°` symbol)
- Added Degree/Radian angle mode support: `sin(`/`cos(`/`tan(` and their inverses now respect the interpreter's angle mode, and the postfix `°`/`r` symbols force degree/radian interpretation for a single value regardless of mode
- Added native support for the `~` negation token, the plaintext ASCII rendering of the calculator's dedicated negation key (same behavior as the `⁻` glyph)
- Added `toString(`, which converts a real number to its string representation (respecting Fix/Float display mode) for concatenation into `Disp`/`Output` strings, and raises `ERR:DATA TYPE` when given a string argument
- Added `IS>(` and `DS<(`, the increment/decrement-and-skip loop-control commands
- Added `Archive`/`UnArchive` as stubs (no-ops, since there's no separate archive memory in this interpreter)
- Added `ClrList` and `ClrAllLists` to clear one or more lists (or every list) to dimension 0, and `prod(` to return the product of all or part of a list, matching `sum(`/`dim(`
- Added an optional strict mode (`Interpreter(..., strict=True)` / `pb -x`) that raises `ExecutionError('ERR:UNDEFINED')` when reading an unset variable, instead of silently defaulting to `0`
- Added `DelVar`, `SortA(`/`SortD(`, `ΔList(`, and `cumSum(`

### Fixed
- Lists can now be specified with an uppercase `L` (e.g. `L1`), matching the lowercase `l` and `∟` glyph forms already supported
- Fixed list/matrix arithmetic (`+`/`-`/`*`/`/`) to be element-wise with scalar broadcasting instead of applying Python's native list/number operators directly
- Fixed `sinh⁻¹(`/`cosh⁻¹(`/`tanh⁻¹(` being unreachable because they were registered under the same tokens as `sin⁻¹(`/`cos⁻¹(`/`tan⁻¹(`, silently shadowing the inverse trig functions
- Fixed `fPart(` returning the integer part instead of the fractional part

## 0.3.0 (2026-07-05)

### Fixed
- Fixed `Goto`/`Lbl` resolving letter+digit labels (e.g. `A1`) to the wrong target
- Fixed `List.set()` raising `IndexError` when storing beyond the current list length
- Added native support for the `⁻` negation glyph
- Fixed multi-row matrix literals being parsed as implied multiplication
- `Menu(` now evaluates title and description expressions before passing them to the I/O backend

## 0.2.0 (2026-07-05)

### Fixed
- Corrected the `prgm` token spelling (was `pgrm`). The parser now correctly recognises sub-program calls written as `prgmNAME`, matching real TI-83/84 BASIC syntax.

## 0.1.0 (2026-07-05)

Initial release. pitybas was originally written by [Ryan Hileman](https://github.com/lunixbochs).

### Added
- TI-BASIC interpreter supporting core language features: variables, arithmetic, control flow (`If`/`Then`/`Else`, `For`, `While`, `Repeat`, `Goto`/`Lbl`), lists, matrices, strings, and math functions
- `simple` and `vt100` I/O backends
- `pb` console script and `python -m pitybas` entry point
- Interactive REPL (run `pb` with no filename)
