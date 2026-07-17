# -*- coding: utf-8 -*-
from typing import Any, Iterator, List, Optional, Union

from . import tokens
from .common import ParseError, is_number
from .expression import (
    Expression,
    Bracketed,
    FunctionArgs,
    Tuple,
    ParenExpr,
    ListExpr,
    MatrixExpr,
)
from .expression import Base as BaseExpression

_SUBSCRIPT_DIGITS = "₀₁₂₃₄₅₆₇₈₉"
_SUBSCRIPT_TRANS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


class Parser:
    LOOKUP = {}
    LOOKUP.update(tokens.Token.tokens)
    LOOKUP.update(tokens.Variable.tokens)
    LOOKUP.update(tokens.Function.tokens)

    SYMBOLS = []
    TOKENS = list(tokens.Token.tokens.keys())
    VARIABLES = list(tokens.Variable.tokens.keys())
    FUNCTIONS = list(tokens.Function.tokens.keys())
    OPERATORS = list(tokens.Operator.tokens.keys())
    TOKENS += VARIABLES + FUNCTIONS

    TOKENS.sort()
    TOKENS.reverse()

    for t in TOKENS:
        if t[0] not in SYMBOLS and not t.isalpha():
            SYMBOLS.append(t[0])

    def __init__(self, source: str) -> None:
        self.source = str(source)
        self.length = len(self.source)
        self.pos = 0
        self.line = 0
        self.lines: List[List[Any]] = []

        self.stack: List[Any] = []

    @staticmethod
    def parse_expr(line: str) -> Any:
        """Parse a bare expression string into its (unevaluated) token tree.

        Unlike :meth:`parse_line`, evaluation is deferred to the caller --
        used to hold a Y1-Y9 equation definition and re-evaluate it fresh on
        each read.  Returns *None* for an empty string.
        """
        if not line:
            return None

        parser = Parser(line)
        parser.TOKENS = parser.VARIABLES + parser.FUNCTIONS + parser.OPERATORS
        # Longest-match-first, same as the top-level parser: otherwise a
        # shorter prefix token wins (e.g. "Y1" would lex as "Y" then "1").
        parser.TOKENS.sort()
        parser.TOKENS.reverse()

        parser.SYMBOLS = []
        for t in parser.TOKENS:
            if t[0] not in parser.SYMBOLS and not t.isalpha():
                parser.SYMBOLS.append(t[0])

        return parser.parse()[0][0]

    @staticmethod
    def parse_line(vm: Any, line: str) -> Any:
        expr = Parser.parse_expr(line)
        if expr is None:
            return None

        return vm.get(expr)

    def clean(self) -> None:
        self.source = self.source.replace("\r\n", "\n").replace("\r", "\n")

    def error(self, msg: str) -> None:
        raise ParseError(msg)

    def _prev_token(self) -> Any:
        """Return the last token in the current expression context.

        Checks the top stack frame first (inside brackets/function args),
        then falls back to the current top-level line.  Returns *None* when
        the current expression is empty (start of a new line or bracket).
        """
        if self.stack:
            contents = getattr(self.stack[-1], "contents", None)
            if contents:
                return contents[-1]
            return None
        if self.lines and self.line < len(self.lines) and self.lines[self.line]:
            return self.lines[self.line][-1]
        return None

    def inc(self, n: int = 1) -> None:
        self.pos += n

    def more(self, pos: Optional[int] = None) -> bool:
        if pos is None:
            pos = self.pos
        return pos < self.length

    def post(self) -> Iterator[List[Any]]:
        for line in self.lines:
            if line:
                new: List[Any] = []
                expr = None
                for token in line:
                    if token.priority > tokens.Pri.INVALID:
                        expr = expr or Expression()
                        expr.append(token)
                    else:
                        if expr:
                            new.append(expr)

                        expr = None
                        new.append(token)

                if expr:
                    new.append(expr)

                if new:
                    # implied expressions need to be added to tuples in their
                    # entirety, instead of just their last element
                    pops = []
                    for i in range(0, len(new) - 1):
                        e, t = new[i], new[i + 1]
                        if isinstance(e, Expression) and isinstance(t, Tuple):
                            pops.append(i)
                            e.append(t.contents[0].flatten())
                            t.contents[0] = e

                    for p in reversed(sorted(pops)):
                        new.pop(p)

                    # tokens with the absorb mechanic can steal the next token
                    # from the line if it matches a list of types
                    last = new[0]
                    pops = []
                    for i in range(1, len(new)):
                        token = new[i]
                        if isinstance(token, last.absorbs):
                            if isinstance(token, BaseExpression):
                                token = token.flatten()

                            last.absorb(token)
                            pops.append(i)

                        last = token

                    for p in reversed(sorted(pops)):
                        new.pop(p)

                yield new

    def parse(self) -> List[List[Any]]:
        while self.more():
            char = self.source[self.pos]
            result: Any = None
            if self.lines and self.lines[-1]:
                token = self.lines[-1][-1]
            else:
                token = None

            if (
                token
                and hasattr(token, "dynamic")
                and hasattr(token.dynamic, "__call__")
                and token.dynamic(char)
            ):
                self.inc()
                continue
            elif char in ("\n", ":"):
                self.close_brackets()

                self.inc()
                self.line += 1
                continue
            elif char in " \t":
                self.inc()
                continue
            elif char in "([{":
                if char == "(":
                    cls: type = ParenExpr
                elif char == "[":
                    if self.more(self.pos + 1) and self.source[self.pos + 1].isalpha():
                        result = self.matrix()
                    else:
                        cls = MatrixExpr
                elif char == "{":
                    cls = ListExpr

                if result is None:
                    self.stack.append(cls(char))
                    self.inc()
                    continue
            elif char in ")]}":
                if self.stack:
                    stacks: List[Any] = []
                    l = len(self.stack)
                    for i in range(l):
                        stack = self.stack.pop(l - i - 1)
                        if isinstance(stack, Bracketed):
                            if stack.close(char):
                                for s in stacks:
                                    stack.append(s)

                                if not isinstance(stack, FunctionArgs):
                                    result = stack

                                stack.finish()
                                self.inc()
                                break
                            elif char != stack.end:
                                self.error(
                                    'tried to end \'%s\' with: "%s" (expecting "%s")'
                                    % (stack, char, stack.end)
                                )
                            else:
                                stacks.append(stack)
                        else:
                            stacks.append(stack)
                else:
                    self.error(
                        'encountered "%s" but we have no expression'
                        " on the stack to terminate" % char
                    )
            elif char == ",":
                if (
                    len(self.stack) > 1
                    and isinstance(self.stack[-2], Tuple)
                    and not isinstance(self.stack[-1], Tuple)
                ):
                    expr = self.stack.pop()
                    tup = self.stack[-1]
                    tup.append(expr)
                    tup.sep()
                elif self.stack and isinstance(self.stack[-1], Tuple):
                    self.stack[-1].sep()
                elif self.stack:
                    raise ParseError(
                        "comma encountered with an unclosed"
                        " non-tuple expression on the stack"
                    )
                else:
                    if self.lines[-1]:
                        token = self.lines[-1].pop()
                    else:
                        self.error(
                            "Encountered comma, but cannot find"
                            " anything to put in the tuple"
                        )

                    tup = Tuple()
                    tup.append(token)
                    self.stack.append(tup)
                    tup.sep()

                if isinstance(self.stack[-1], FunctionArgs):
                    self.stack.append(Expression())

                self.inc()
                continue
            elif char.isdigit() and self.token(sub=True, inc=False) is not None:
                # word-command tokens that begin with a digit (e.g.
                # "1-Var Stats") must be matched whole, before the numeric
                # branch below claims the leading digit as a number literal.
                result = self.token()
            elif (
                "0" <= char <= "9"
                or char == "."
                or (
                    isinstance(self.token(sub=True, inc=False), tokens.Minus)
                    and self.number(test=True)
                    and not getattr(self._prev_token(), "can_fill_right", False)
                )
            ):
                result = tokens.Value(self.number())
            elif (
                char in "lL∟ʟ"
                and self.more(self.pos + 1)
                and self.source[self.pos + 1]
                in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" + _SUBSCRIPT_DIGITS
            ):
                result = self.list()
            elif char.isalpha():
                result = self.token()
            elif char == '"':
                # " is ambiguous: it's both the string-quote token and the
                # DMS seconds symbol (30°15'20"). Only treat it as DMS
                # seconds when it directly follows a minutes value (')  -
                # otherwise it opens a string, same as always.
                if self.dms_seconds_pending():
                    result = self.symbol()
                else:
                    result = tokens.Value(self.string())
            elif char in self.SYMBOLS:
                result = self.symbol()
            else:
                self.error("could not tokenize: %s" % repr(char))

            if isinstance(result, tokens.Stor):
                self.close_brackets()

            if result is not None:
                self.add(result)

            argument = False
            if isinstance(result, tokens.Function):
                argument = True

            if isinstance(result, (tokens.List, tokens.Matrix)):
                if self.more() and self.source[self.pos] == "(":
                    self.inc()
                    argument = True

            # we were told to push the stack into argument mode
            if argument:
                args = FunctionArgs("(")
                self.stack.append(args)
                self.stack.append(Expression())
                result.absorb(args)

        self.close_brackets()
        return [line for line in self.post()]

    def add(self, token: Any) -> None:
        # TODO: cannot add Pri.INVALID unless there's no expr on the stack
        if isinstance(token, FunctionArgs):
            # already linked to its owning Function/List/Matrix via the
            # .absorb() call made when it was pushed onto the stack; adding
            # it again here (e.g. via close_brackets() implicitly closing
            # an unclosed call at end of line) would duplicate it as a
            # sibling of its own owner.
            return

        if self.stack:
            stack = self.stack[-1]
            stack.append(token)
        else:
            while self.line >= len(self.lines):
                self.lines.append([])

            self.lines[self.line].append(token)

    def close_brackets(self) -> None:
        while self.stack:
            self.add(self.stack.pop())

    def dms_seconds_pending(self) -> bool:
        items: Optional[List[Any]]
        if self.stack:
            items = getattr(self.stack[-1], "contents", None)
        elif self.lines and self.line < len(self.lines):
            items = self.lines[self.line]
        else:
            items = None

        return (
            items is not None
            and len(items) >= 2
            and isinstance(items[-2], tokens.MinuteSymbol)
        )

    def symbol(self) -> Optional[Any]:
        token = self.token(True)
        if token:
            return token
        else:
            char = self.source[self.pos]
            if char in self.LOOKUP:
                self.inc()
                return self.LOOKUP[char]()
            else:
                # a second time to throw the error
                self.token()
                return None

    def token(self, sub: bool = False, inc: bool = True) -> Optional[Any]:
        remaining = self.source[self.pos :]
        for token in self.TOKENS:
            if remaining.startswith(token):
                if inc:
                    self.inc(len(token))
                return self.LOOKUP[token]()
        else:
            if not sub:
                near = remaining[:8].split("\n", 1)[0]
                self.error(
                    'no token found at pos %i near "%s"' % (self.pos, repr(near))
                )
            return None

    def number(
        self, dot: bool = True, test: bool = False, inc: bool = True
    ) -> Union[bool, int, float]:
        num = ""
        first = True
        pos = self.pos
        while self.more(pos):
            char = self.source[pos]
            if char == "-" and first:
                pass
            elif not char.isdigit():
                break

            first = False
            num += char
            pos += 1

        if char == "." and dot:
            num += "."
            pos += 1

            self.pos, tmp = pos, self.pos
            try:
                num += str(self.number(dot=False))
            except ParseError:
                pass

            pos, self.pos = self.pos, tmp

        if inc and not test:
            self.pos = pos

        if is_number(num):
            if test:
                return True
            n: Union[int, float]
            try:
                n = int(num)
            except ValueError:
                n = float(num)

            return n
        else:
            if test:
                return False
            lines = self.source[:pos]
            line = lines.count("\n") + 1
            col = max(self.pos - lines.rfind("\n"), 0)
            raise ParseError(
                "invalid number ending at {}:{}: {}".format(line, col, num)
            )

    def string(self) -> str:
        ret = ""
        self.inc()

        while self.more():
            char = self.source[self.pos]
            if char == '"':
                self.inc()
                break

            elif char == "\n":
                break

            elif char == "→":
                # STO terminates an unclosed string literal -- the closing
                # quote is optional on real hardware, so `"HELLO→Str1` and
                # `"X²→Y1` store the string's contents.  Leave → in place so
                # it tokenizes as the Stor that follows.
                break

            ret += char
            self.inc()

        return ret

    def all(self, match: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") -> str:
        ret = ""
        while self.more():
            char = self.source[self.pos]
            if char in match:
                ret += char
                self.inc()
            else:
                break

        return ret

    def list(self) -> Any:
        self.inc()
        name = self.all(
            match="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" + _SUBSCRIPT_DIGITS
        )
        name = name.translate(_SUBSCRIPT_TRANS)
        return tokens.List(name)

    def matrix(self) -> Any:
        self.inc()
        name = self.all()

        assert self.more() and self.source[self.pos] == "]"
        self.inc()

        return tokens.Matrix(name)
