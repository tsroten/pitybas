pitybas
=======
A working TI-BASIC interpreter, written in Python.

Currently, all `.bas` files in tests/ run except circle.bas (due to lack of graph screen functions)

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

You can also run it as a module without installing the console script:

    python -m pitybas -i vt100

## Development

Clone the repository and install it in editable mode with the test extras:

    pip install -e .[test]
    pytest
