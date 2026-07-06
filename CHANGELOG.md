# Changelog

## Unreleased

### Added
- Added `IS>(` and `DS<(`, the increment/decrement-and-skip loop-control commands
- Added `Archive`/`UnArchive` as stubs (no-ops, since there's no separate archive memory in this interpreter)

### Fixed
- Lists can now be specified with an uppercase `L` (e.g. `L1`), matching the lowercase `l` and `∟` glyph forms already supported

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
