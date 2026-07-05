import copy

import pytest

from pitybas.interpret import Interpreter
from pitybas.parse import Parser


class MockIO:
    """An IO backend that records output and serves canned input, so tests
    can drive a program without touching stdin/stdout."""

    def __init__(self, vm, inputs=None):
        self.vm = vm
        self.disps = []
        self.outputs = []
        self.clears = 0
        self.inputs = list(inputs or [])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def clear(self):
        self.clears += 1

    def input(self, msg, is_str=False):
        val = self.inputs.pop(0)
        if not is_str and isinstance(val, str):
            val = Parser.parse_line(self.vm, val)
        return val

    def getkey(self):
        raise NotImplementedError

    def output(self, x, y, msg):
        self.outputs.append((x, y, msg))

    def disp(self, msg=''):
        # lists/matrices are mutable and stored by reference in the vm;
        # snapshot them so later mutations don't retroactively change
        # already-recorded output.
        self.disps.append(copy.deepcopy(msg))

    def pause(self, msg=''):
        if msg:
            self.disp(msg)

    def menu(self, menu):
        raise NotImplementedError


def make_vm(source, inputs=None, **kwargs):
    return Interpreter.from_string(source, io=lambda vm: MockIO(vm, inputs), **kwargs)


def run(source, inputs=None, **kwargs):
    """Parse and execute a snippet of TI-BASIC source, returning the vm."""
    vm = make_vm(source, inputs=inputs, **kwargs)
    vm.execute()
    return vm


@pytest.fixture
def vm_factory():
    return make_vm


@pytest.fixture
def run_source():
    return run
