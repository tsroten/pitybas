from pitybas.common import Error, is_number


def test_error_str_returns_msg():
    assert str(Error('something broke')) == 'something broke'


def test_is_number_accepts_integers():
    assert is_number('123')
    assert is_number('0')


def test_is_number_accepts_negative_integers():
    assert is_number('-123')


def test_is_number_accepts_decimals():
    assert is_number('1.5')
    assert is_number('-1.5')


def test_is_number_rejects_non_numeric():
    assert not is_number('abc')
    assert not is_number('1.2.3')
    assert not is_number('')


def test_is_number_accepts_non_string_input():
    assert is_number(42)
    assert is_number(-3.14)
