# Changelog

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
