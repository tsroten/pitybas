# Changelog

## Unreleased

### Added
- Added the `⁻¹` postfix operator (multiplicative inverse): `n⁻¹` evaluates to `1/n`
- Added the `×√` infix operator (general nth root): `n×√x` evaluates to the nth root of x
- Added graph screen support: a 95x63-pixel `GraphState` with window variables (`Xmin`/`Xmax`/`Xscl`/`Ymin`/`Ymax`/`Yscl`/`AxesOn`/`AxesOff`), point/pixel drawing (`Pt-On(`/`Pt-Off(`/`Pt-Change(`/`Pxl-On(`/`Pxl-Off(`/`Pxl-Change(`/`Pxl-Test(`/`ClrDraw`), geometric drawing (`Line(`, `Circle(`, `Horizontal`, `Vertical`), function/region plotting (`DrawF`, `Shade(`), text placement (`Text(`), and zoom presets (`ZStandard`, `ZDecimal`). The `vt100` IO backend (`pb -i vt100`) renders the graph screen live as a 48x16 grid of Unicode Braille characters and holds the screen at program exit if it was the most recently active screen, matching real TI-83/84 behavior; the `simple` backend and `ScriptedIO` track pixel state without rendering (see README "Known Limitations" — `Text(` doesn't render visibly under any backend yet)
- Added `StorePic`/`RecallPic` and `StoreGDB`/`RecallGDB` to snapshot the pixel buffer and graph window variables to/from numbered slots (0-9)
- Added `ScriptedIO`, a public `pitybas.io` backend for headlessly driving a program in tests and asserting on what it displayed/drew (replaces the test-only `MockIO`)
- Added an `IOBase` abstract base class formalizing the IO backend contract shared by `simple`/`vt100`/`ScriptedIO`

### Changed
- Bumped supported Python versions to 3.11–3.14 (`requires-python = ">=3.11"`), updated Trove classifiers, updated mypy target to 3.11, and updated GitHub Actions test matrix and build/lint/publish jobs to target 3.11–3.14

### Fixed
- Fixed `nPr` and `nCr` to support scalar/list broadcasting and pairwise same-length list arguments while rejecting mismatched list dimensions and matrix operands with TI-BASIC errors
- Fixed `inString(` using Python's 0-based indexing and `-1` not-found sentinel instead of TI's 1-based semantics: a match now returns a 1-based character position (e.g. `inString("PQRSTUV","STU")` returns `4`), the optional `start` argument is interpreted as a 1-based position, a missing substring (or a `start` past the end of the string) returns `0` rather than `-1`, and a `start` below `1` now raises `ERR:DOMAIN` instead of being passed through as a negative (search-from-end) offset
- Fixed the `×√` operator returning floating-point noise for perfect roots (e.g. `3×√1000` now returns exactly `10`) and raising a Python complex-number error instead of `ERR:NONREAL ANS` for even roots of negative numbers
- Fixed `StorePic`/`RecallPic`/`StoreGDB`/`RecallGDB` raising a bare `AssertionError` (silently disabled under `python -O`) instead of `ERR:DOMAIN` for out-of-range or non-integer slot numbers
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
