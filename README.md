pitybas
=======
A working TI-BASIC interpreter, written in Python.

## Installation

    pip install pitybas

## Usage

Use `pb -i vt100` to run programs which need a working home screen.

If you run `pb` with no filename, it launches an interactive shell.

    Usage: pb [options] filename

    Options:
        -h, --help        show this help message and exit
        -a, --ast         parse, print ast, and quit
        -d, --dump        dump variables in stacktrace
        -s, --stacktrace  always stacktrace
        -v, --verbose     verbose output
        -i IO, --io=IO    select an IO system: simple (default), vt100
        -x, --strict      raise ERR:UNDEFINED instead of silently defaulting unset variables to 0

You can also run it as a module without installing the console script:

    python -m pitybas -i vt100

## Testing Programs

`pitybas` ships a `ScriptedIO` backend that lets you drive programs in tests
without touching `stdin`/`stdout`.  Pass it as the `io` argument to
`Interpreter`, pre-supply canned inputs (consumed by `Input`, `Prompt`, and
`Menu` instructions in order), and inspect the recorded output afterwards.

```python
from pitybas.interpret import Interpreter
from pitybas.io.scripted import ScriptedIO

vm = Interpreter.from_string(
    'Input A\nDisp A*2',
    io=lambda vm: ScriptedIO(vm, inputs=['21']),
)
vm.execute()
assert vm.io.disps == [42]   # recorded disp output
```

`ScriptedIO` also accepts a `keys` list for programs that poll `getKey`; once
the list is exhausted, `getKey` returns `0` (no key held), which naturally
lets timeout-based polling loops run out.

Recorded attributes:

| Attribute | Contents |
|-----------|----------|
| `disps`   | Values passed to `Disp`, in order |
| `outputs` | `(row, col, msg)` tuples from `Output()` calls |
| `clears`  | Number of `ClrHome` calls |

## Known Limitations

- **Graph screen functions are not supported.** Commands that draw to the TI-83/84 graph screen (e.g. `Circle`, `Line`, `DrawF`) are not implemented. Programs that use them will fail or produce no output.

## Development

Clone the repository and install it in editable mode with the test extras:

    pip install -e .[test]
    pytest
