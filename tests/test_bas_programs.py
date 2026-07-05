"""Smoke tests that run the sample .bas programs in tests/ end-to-end and
just check that they execute without raising. These files were previously
only exercised by eyeballing their output when run manually via pb.py.
"""
import os

import pytest

from conftest import make_vm

TESTS_DIR = os.path.dirname(__file__)


def load(name):
    with open(os.path.join(TESTS_DIR, name), encoding='utf8') as f:
        return f.read()


@pytest.mark.parametrize('filename', [
    'blocks.bas',
    'generic.bas',
    'listmat.bas',
    'logic.bas',
    'math.bas',
])
def test_bas_program_runs_without_error(filename):
    vm = make_vm(load(filename))
    vm.execute()
    assert vm.io.disps


def test_trig_bas_runs_with_prompted_input():
    # C is 5, and "C > 10 + 1" evaluates the addition before the
    # comparison (addition binds tighter than relational operators, as on
    # a real TI calculator), i.e. 5 > 11, so the Else branch runs.
    vm = make_vm(load('trig.bas'), inputs=['3', '4'])
    vm.execute()
    assert vm.io.disps == [5, 'Smaller than 11', 4, 5]


@pytest.mark.skip(reason='circle.bas needs graph-screen functions (Pt-On) not implemented by any IO backend; see README')
def test_circle_bas_runs_without_error():
    vm = make_vm(load('circle.bas'))
    vm.execute()


@pytest.mark.skip(reason='getkey.bas needs a real getKey() implementation; MockIO.getkey() raises NotImplementedError by design')
def test_getkey_bas_runs_without_error():
    vm = make_vm(load('getkey.bas'))
    vm.execute()


@pytest.mark.skip(reason='menu.bas needs a real menu() implementation; MockIO.menu() raises NotImplementedError by design')
def test_menu_bas_runs_without_error():
    vm = make_vm(load('menu.bas'))
    vm.execute()
