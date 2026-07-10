# Changelog

## Unreleased

### Added
- Added the `⁻¹` postfix operator (multiplicative inverse): `n⁻¹` evaluates to `1/n`
- Added the `×√` infix operator (general nth root): `n×√x` evaluates to the nth root of x

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
