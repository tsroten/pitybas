import copy

from pitybas.io.base import IOBase
from pitybas.parse import Parser


class MockIO(IOBase):
    """An IO backend that records output and serves canned input, so tests
    can drive a program without touching stdin/stdout."""

    def __init__(self, vm, inputs=None):
        self.vm = vm
        self.disps = []
        self.outputs = []
        self.clears = 0
        self.inputs = list(inputs or [])

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
