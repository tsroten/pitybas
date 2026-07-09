from pitybas import tokens


def test_core_token_types_are_re_exported():
    assert issubclass(tokens.Token, tokens.Parent)
    assert issubclass(tokens.Variable, tokens.Parent)
    assert issubclass(tokens.Function, tokens.Parent)
    assert tokens.get is not None


def test_dynamic_variable_class_remains_in_tokens_namespace():
    assert hasattr(tokens, 'A')
    assert issubclass(tokens.A, tokens.NumVar)
