import pytest

from mock_io import MockIO
from pitybas.interpret import Interpreter


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
