"""Tests for pitybas.io.base.IOBase, the abstract IO base class."""

import pytest

from pitybas.interpret import Interpreter
from pitybas.io.base import IOBase
from pitybas.io.simple import IO as SimpleIO
from pitybas.io.vt100 import IO as VT100IO


def test_iobase_is_abstract():
    """IOBase cannot be instantiated directly."""
    vm = Interpreter.from_string('')
    with pytest.raises(TypeError):
        IOBase(vm)


def test_iobase_requires_all_abstract_methods():
    """A subclass that omits even one abstract method cannot be instantiated."""
    class Incomplete(IOBase):
        def clear(self): pass
        def input(self, msg, is_str=False): pass
        def getkey(self): pass
        def output(self, row, col, msg): pass
        def disp(self, msg=''): pass
        def pause(self, msg=''): pass
        # menu is intentionally omitted

    vm = Interpreter.from_string('')
    with pytest.raises(TypeError):
        Incomplete(vm)


def test_simple_io_is_subclass_of_iobase():
    assert issubclass(SimpleIO, IOBase)


def test_vt100_io_is_subclass_of_iobase():
    assert issubclass(VT100IO, IOBase)


def test_iobase_enter_returns_self():
    """The default __enter__ implementation returns self."""
    class Concrete(IOBase):
        def clear(self): pass
        def input(self, msg, is_str=False): pass
        def getkey(self): pass
        def output(self, row, col, msg): pass
        def disp(self, msg=''): pass
        def pause(self, msg=''): pass
        def menu(self, menu): pass

    vm = Interpreter.from_string('')
    obj = Concrete(vm)
    assert obj.__enter__() is obj


def test_iobase_exit_does_not_raise():
    """The default __exit__ implementation is a no-op."""
    class Concrete(IOBase):
        def clear(self): pass
        def input(self, msg, is_str=False): pass
        def getkey(self): pass
        def output(self, row, col, msg): pass
        def disp(self, msg=''): pass
        def pause(self, msg=''): pass
        def menu(self, menu): pass

    vm = Interpreter.from_string('')
    obj = Concrete(vm)
    obj.__exit__(None, None, None)  # should not raise


def test_iobase_stores_vm():
    """The default __init__ stores the vm attribute."""
    class Concrete(IOBase):
        def clear(self): pass
        def input(self, msg, is_str=False): pass
        def getkey(self): pass
        def output(self, row, col, msg): pass
        def disp(self, msg=''): pass
        def pause(self, msg=''): pass
        def menu(self, menu): pass

    vm = Interpreter.from_string('')
    obj = Concrete(vm)
    assert obj.vm is vm
