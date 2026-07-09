import pytest

from pitybas.interpret import Interpreter
from pitybas.io.scripted import ScriptedIO


def make_vm(source, inputs=None, **kwargs):
    return Interpreter.from_string(source, io=lambda vm: ScriptedIO(vm, inputs), **kwargs)


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
