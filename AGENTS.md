# pitybas

A TI-BASIC interpreter written in Python (targets TI-83/84 Plus dialect). Source lives in
`src/pitybas/`; `pb` (or `python -m pitybas`) is the CLI entry point (`src/pitybas/cli.py`).

The main reason someone reaches for this library is to **automate tests of their own
TI-BASIC programs** — drive a `.bas` program headlessly and assert on what it displayed,
without a real calculator or manual key-pressing. That workflow is the priority below.

**Every change to `src/pitybas/` — new tokens, bug fixes, behavior changes — needs a
corresponding entry under `## Unreleased` in `CHANGELOG.md` in the same change.** This
repo treats the changelog as the source of truth for what shipped (see "Release process"
below); it's not optional bookkeeping reserved for features.

## Testing a TI-BASIC program: the pattern

```python
from pitybas.interpret import Interpreter
from pitybas.io.scripted import ScriptedIO

vm = Interpreter.from_string(
    source,  # or Interpreter.from_file("PROGRAM.bas")
    io=lambda vm: ScriptedIO(vm, inputs=["21"], keys=[105, 105, 0]),
)
vm.execute()
assert vm.io.disps == [42]
```

`io` must be a callable `vm -> IOBase`, not an instance — `Interpreter.__init__` calls
`io(self)`. `ScriptedIO` (`src/pitybas/io/scripted.py`) is the backend built for this —
see its class docstring for the full list of recorded attributes (`disps`, `outputs`,
`draws`, etc.). Existing `.bas` fixtures under `tests/` (`tests/*.bas`, driven from
`tests/test_bas_programs.py`) are good references for how a new test program should look.

Non-obvious things that will bite you when writing test assertions:

- **The default `simple` backend's `getKey` raises `NotImplementedError`.** Any program
  that polls `getKey` (basically every real-time/game-loop program) needs `ScriptedIO` or
  the `vt100` backend — never the plain `IO` — or `vm.execute()` will crash.
- **`Interpreter.get()` collapses whole-number floats/complex to `int`.** `5.0` displays
  as `5`, and a real result with zero imaginary part displays as its real part. Write
  assertions as `== [42]`, not `== [42.0]`.
- **`ScriptedIO.disp()` deep-copies its argument** so later mutations to `vm.lists`/
  `vm.matrix` (stored by reference) don't retroactively change already-recorded `disps`.
- **`inputs` is one shared queue** consumed by `Input`, `Prompt`, *and* `Menu` in the
  order the program executes them — not separate lists per instruction. `Menu` pops a
  1-based index into the flattened list of all options across all groups.
- **Colons and newlines are equivalent statement separators** at parse time — `"Disp
  1:Disp 2"` and `"Disp 1\nDisp 2"` produce the same two-statement program, so either can
  be used to build test fixtures inline.
- **Errors surface as `pitybas.common.ExecutionError`** with a real TI error string (e.g.
  `"ERR:DOMAIN"`) as `.msg`/`str(e)`. Assert with `pytest.raises(ExecutionError,
  match="ERR:...")`.
- **`Interpreter(..., strict=True)`** (or `pb -x`) raises `ERR:UNDEFINED` on reading an
  unset variable instead of silently defaulting it to `0` — useful for catching a test
  program that relies on calculator memory state you didn't intend to provide.
- **`prgmNAME` sub-calls resolve by scanning the *current working directory*** for a
  case-insensitively matching `<name>.bas` (`Interpreter.run_prgm`) — not relative to the
  calling program's own file. Programs that call other programs need their `cwd` set
  accordingly, and this only works with `Interpreter.from_file`, not `from_string`.
- **Graph-screen output only visibly renders under the `vt100` backend**; `simple` and
  `ScriptedIO` just track pixel state / record calls. For test assertions on drawing, read
  `ScriptedIO`'s `draws`/`lines`/`circles`/`pxls` records instead.
- **`Text(` doesn't render under any backend yet** (only calls `draw_text_graph`,
  recorded in `ScriptedIO.texts`) — see README "Known Limitations" for why.

## Interpreter internals worth knowing before debugging odd output

- Expression operator precedence is driven by `common.Pri`, not source order — see
  `Base.order()` in `expression.py`.
- `vm.print_ast()` / `vm.print_tokens()` / `vm.print_stacktrace()` are the fastest way to
  see how a program actually parsed when behavior looks wrong; `pb -a file.bas` prints
  the AST and quits, `pb -s` always stacktraces.
- `tests/test_known_bugs.py` documents real historical bugs (with root cause) as
  regression tests — worth checking before assuming a piece of parsing/eval behavior is
  intentional vs. something that was already found and fixed once.

## Adding/fixing a TI-BASIC token (when a test program uses something unsupported)

Tokens self-register via the `Tracker` metaclass (`token_core.py`): a class body simply
needs a `run`/`get`/`set`/`fill_left`/`fill_right` method and it's auto-flagged
`can_run`/`can_get`/etc. — there's no separate registration call. The lookup key defaults
to the class name; override with a class attribute `token = "..."` when the TI-BASIC
spelling isn't a valid Python identifier. `Function` subclasses get `(` appended to their
key automatically. Nearly all tokens live in `src/pitybas/tokens.py` (2300+ lines — grep
for a similar existing token rather than reading it top to bottom). `TODO.md` lists known
missing tokens/features and *why* they're hard. Don't forget the CHANGELOG entry (see
above).

## Dev workflow

```
pip install -e ".[test,lint]"
python -m pytest
ruff check src/ tests/
ruff format src/ tests/
mypy                            # only checks src/pitybas, not tests/
```

CI (`.github/workflows/tests.yml`) runs pytest across Python 3.9–3.12 — don't rely on
3.13+-only stdlib behavior in `src/`.

## Release process

Version lives in `src/pitybas/__init__.py` (`__version__`), read dynamically by
`pyproject.toml`. A release commit bumps that string and moves the `## Unreleased`
CHANGELOG section into a new `## X.Y.Z (YYYY-MM-DD)` section in the same commit. Pushing a
`vX.Y.Z` tag triggers `.github/workflows/publish.yml`, which builds and publishes to
PyPI — tagging is effectively "ship it," so don't tag as a side effect of unrelated work.
