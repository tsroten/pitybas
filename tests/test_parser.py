import pytest

from pitybas.parse import Parser
from pitybas.common import ParseError
from pitybas import tokens
from pitybas.expression import Expression


def test_parse_integer_literal():
    code = Parser("42").parse()
    expr = code[0][0]
    assert isinstance(expr, Expression)
    assert expr.contents[0].value == 42
    assert isinstance(expr.contents[0].value, int)


def test_parse_float_literal():
    code = Parser("1.5").parse()
    value = code[0][0].contents[0].value
    assert value == 1.5
    assert isinstance(value, float)


def test_parse_negative_number():
    code = Parser("-5").parse()
    value = code[0][0].contents[0].value
    assert value == -5


def test_parse_string_literal():
    code = Parser('"hello"').parse()
    assert code[0][0].contents[0].value == "hello"


def test_parse_unterminated_string_stops_at_newline():
    code = Parser('"hello\nDisp 1').parse()
    assert code[0][0].contents[0].value == "hello"


def test_parse_expression_tokens():
    code = Parser("1+2").parse()
    expr = code[0][0]
    values = [t.value if hasattr(t, "value") else t.token for t in expr.contents]
    assert values == [1, "+", 2]


def test_parse_implied_multiplication():
    code = Parser("2A").parse()
    expr = code[0][0]
    assert isinstance(expr.contents[1], tokens.Mult)


def test_parse_multiple_lines():
    code = Parser("Disp 1\nDisp 2").parse()
    assert len(code) == 2
    assert isinstance(code[0][0], tokens.Disp)
    assert isinstance(code[1][0], tokens.Disp)


def test_parse_colon_separates_lines():
    code = Parser("Disp 1:Disp 2").parse()
    assert len(code) == 2


def test_parse_invalid_character_raises():
    with pytest.raises(ParseError):
        Parser("@").parse()


def test_parse_line_helper_evaluates_expression():
    from pitybas.interpret import Interpreter

    vm = Interpreter.from_string("1->A")
    vm.execute()
    result = Parser.parse_line(vm, "A+1")
    assert result == 2


def test_prgm_parses_to_correct_token():
    code = Parser("prgmFOO").parse()
    token = code[0][0]
    assert isinstance(token, tokens.prgm)
    assert token.name == "FOO"


def test_pgrm_misspelling_raises_parse_error():
    # 'pgrm' (letters transposed) is not a valid token; the correct spelling
    # is 'prgm'. The parser should reject it rather than silently misfire.
    from pitybas.common import ParseError

    with pytest.raises(ParseError):
        Parser("pgrm").parse()
