import pytest

from conftest import run
from pitybas.common import ExecutionError


def test_set_and_get_date():
    vm = run('setDate(2020,7,4)\nDisp getDate')
    assert vm.io.disps == [[2020, 7, 4]]


def test_set_and_get_time():
    vm = run('setTime(13,25,30)\nDisp getTime')
    assert vm.io.disps == [[13, 25, 30]]


def test_set_date_preserves_time():
    vm = run('setTime(13,25,30)\nsetDate(2020,7,4)\nDisp getTime')
    assert vm.io.disps == [[13, 25, 30]]


def test_set_time_preserves_date():
    vm = run('setDate(2020,7,4)\nsetTime(13,25,30)\nDisp getDate')
    assert vm.io.disps == [[2020, 7, 4]]


def test_get_dt_str_formats():
    vm = run('''
setDate(2020,7,4)
Disp getDtStr(1)
Disp getDtStr(2)
Disp getDtStr(3)
''')
    assert vm.io.disps == ['07/04/20', '04/07/20', '20/07/04']


def test_get_dt_str_uses_dt_fmt_variable():
    vm = run('setDate(2020,7,4)\nsetDtFmt(2)\nDisp getDtStr(getDtFmt)')
    assert vm.io.disps == ['04/07/20']


def test_get_tm_str_formats():
    vm = run('''
setTime(13,25,30)
Disp getTmStr(24)
Disp getTmStr(12)
''')
    assert vm.io.disps == ['13:25', '1:25 PM']


def test_get_tm_str_midnight_and_noon_are_12():
    vm = run('''
setTime(0,5,0)
Disp getTmStr(12)
setTime(12,5,0)
Disp getTmStr(12)
''')
    assert vm.io.disps == ['12:05 AM', '12:05 PM']


def test_dt_fmt_round_trip():
    vm = run('setDtFmt(2)\nDisp getDtFmt')
    assert vm.io.disps == [2]


def test_tm_fmt_round_trip():
    vm = run('setTmFmt(24)\nDisp getTmFmt')
    assert vm.io.disps == [24]


def test_set_dt_fmt_rejects_invalid_value():
    with pytest.raises(ExecutionError, match='ERR:ARGUMENT'):
        run('setDtFmt(4)')


def test_set_tm_fmt_rejects_invalid_value():
    with pytest.raises(ExecutionError, match='ERR:ARGUMENT'):
        run('setTmFmt(3)')


def test_time_cnv():
    vm = run('Disp timeCnv(90061)')
    assert vm.io.disps == [[1, 1, 1, 1]]


def test_check_tmr_uses_start_tmr_baseline():
    vm = run('startTmr->A\ncheckTmr(A->B\nDisp B')
    assert vm.io.disps[0] >= 0


def test_day_of_wk():
    # July 4, 2020 was a Saturday (7 in TI's 1=Sunday..7=Saturday encoding)
    vm = run('Disp dayOfWk(2020,7,4)')
    assert vm.io.disps == [7]
