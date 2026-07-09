from pitybas import tokens


def test_core_token_types_are_re_exported():
    assert issubclass(tokens.Token, tokens.Parent)
    assert issubclass(tokens.Variable, tokens.Parent)
    assert issubclass(tokens.Function, tokens.Parent)
    assert tokens.get is not None


def test_dynamically_generated_variable_a_accessible():
    assert hasattr(tokens, 'A')
    assert issubclass(tokens.A, tokens.NumVar)
